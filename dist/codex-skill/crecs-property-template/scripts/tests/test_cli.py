"""Contract for the command line: --help everywhere, actionable errors, and the
export gate.

These run the CLI in-process through its main() so that exit codes and stdout are
part of the contract.
"""

import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from crecs import cli

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
BASE_TEMPLATE = os.path.join(SKILL_ROOT, "assets", "property-template-all-widgets.json")
PROFILE_EXAMPLE = os.path.join(SKILL_ROOT, "assets", "target-profile.example.json")
# A profile that is complete for the shipped template. The EXAMPLE deliberately is not:
# it no longer declares the reference site's popup ids, because doing so let a copied
# profile validate clean with two dead buttons (delivery-3 defect D3-B2).
PROFILE_FIXTURE = os.path.join(HERE, "fixtures", "target-profile.test.json")

COMMANDS = [
    "init", "inspect", "set", "unset", "add-widget", "remove", "move",
    "bind", "unbind", "validate", "diff", "history", "undo", "export",
    "catalog", "selftest",
]


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class TestHelp(unittest.TestCase):
    def test_top_level_help(self):
        code, out, _ = run_cli("--help")
        self.assertEqual(code, 0)
        for name in COMMANDS:
            self.assertIn(name, out)

    def test_every_command_has_help(self):
        for name in COMMANDS:
            code, out, _ = run_cli(name, "--help")
            self.assertEqual(code, 0, name)
            self.assertIn("usage", out.lower(), name)

    def test_unknown_command_is_actionable(self):
        code, out, err = run_cli("frobnicate")
        self.assertNotEqual(code, 0)
        self.assertIn("frobnicate", out + err)


class WorkdirCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def init(self, *extra):
        return run_cli("init", "--from", BASE_TEMPLATE, "--workdir", self.wd, *extra)


class TestInitAndInspect(WorkdirCase):
    def test_init_from_the_shipped_base_template(self):
        code, out, err = self.init()
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.wd, "document.json")))

    def test_init_reports_the_revision_and_hash(self):
        _, out, _ = self.init()
        self.assertIn("revision", out.lower())

    def test_inspect_lists_widgets(self):
        self.init()
        code, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets")
        self.assertEqual(code, 0)
        self.assertIn("crecs_property_data", out)

    def test_inspect_json_is_machine_readable(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        json.loads(out)

    def test_inspect_tree_shows_nesting(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--tree")
        self.assertIn("section", out)
        self.assertIn("column", out)

    def test_inspect_a_single_element(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        loader = [w for w in json.loads(out)["widgets"]
                  if w["widgetType"] == "crecs_property_data"][0]
        _, detail, _ = run_cli("inspect", "--workdir", self.wd,
                               "--element", loader["id"], "--json")
        self.assertIn("settings", json.loads(detail))

    def test_missing_workdir_tells_you_to_init(self):
        code, out, err = run_cli("inspect", "--workdir", os.path.join(self.tmp, "nope"))
        self.assertNotEqual(code, 0)
        self.assertIn("init", (out + err).lower())


class TestEditing(WorkdirCase):
    def widget_id(self, widget_type):
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        for w in json.loads(out)["widgets"]:
            if w["widgetType"] == widget_type:
                return w["id"]
        raise AssertionError("widget not present: " + widget_type)

    def test_set_a_colour(self):
        self.init()
        wid = self.widget_id("crecs_property_fields")
        code, out, err = run_cli("set", "--workdir", self.wd, "--element", wid,
                                 "--key", "card_color", "--value", "#123456")
        self.assertEqual(code, 0, out + err)
        _, detail, _ = run_cli("inspect", "--workdir", self.wd, "--element", wid, "--json")
        self.assertEqual(json.loads(detail)["settings"]["card_color"], "#123456")

    def test_set_rejects_an_invented_key_before_writing(self):
        self.init()
        wid = self.widget_id("crecs_property_fields")
        code, out, err = run_cli("set", "--workdir", self.wd, "--element", wid,
                                 "--key", "card_glow", "--value", "5")
        self.assertNotEqual(code, 0)
        self.assertIn("card_glow", out + err)
        _, detail, _ = run_cli("inspect", "--workdir", self.wd, "--element", wid, "--json")
        self.assertNotIn("card_glow", json.loads(detail)["settings"])

    def test_set_with_device_writes_the_suffixed_key(self):
        self.init()
        wid = self.widget_id("crecs_property_fields")
        value = json.dumps({"unit": "px", "top": "4", "right": "4", "bottom": "4",
                            "left": "4", "isLinked": True})
        code, out, err = run_cli("set", "--workdir", self.wd, "--element", wid,
                                 "--key", "card_margin", "--device", "mobile",
                                 "--value", value)
        self.assertEqual(code, 0, out + err)
        _, detail, _ = run_cli("inspect", "--workdir", self.wd, "--element", wid, "--json")
        self.assertIn("card_margin_mobile", json.loads(detail)["settings"])

    def test_set_with_device_on_a_non_responsive_control_is_refused(self):
        self.init()
        wid = self.widget_id("crecs_property_fields")
        code, out, err = run_cli("set", "--workdir", self.wd, "--element", wid,
                                 "--key", "card_color", "--device", "mobile",
                                 "--value", "#fff")
        self.assertNotEqual(code, 0)
        self.assertIn("responsive", (out + err).lower())

    def test_value_types_are_preserved(self):
        self.init()
        wid = self.widget_id("crecs_property_fields")
        run_cli("set", "--workdir", self.wd, "--element", wid,
                "--key", "show_label", "--value", "")
        _, detail, _ = run_cli("inspect", "--workdir", self.wd, "--element", wid, "--json")
        self.assertEqual(json.loads(detail)["settings"]["show_label"], "")

    def test_add_widget_and_remove_it(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--tree", "--json")
        column = [e for e in json.loads(out)["elements"] if e["elType"] == "column"][0]
        code, out, err = run_cli("add-widget", "--workdir", self.wd,
                                 "--widget", "crecs_property_rates",
                                 "--into", column["id"])
        self.assertEqual(code, 0, out + err)
        new_id = json.loads(out)["element_id"] if out.strip().startswith("{") else None
        if new_id is None:
            new_id = self.widget_id("crecs_property_rates")
        code, out, err = run_cli("remove", "--workdir", self.wd, "--element", new_id,
                                 "--reason", "not needed for this client")
        self.assertEqual(code, 0, out + err)

    def test_removing_the_loader_requires_force_and_explains_why(self):
        self.init()
        wid = self.widget_id("crecs_property_data")
        code, out, err = run_cli("remove", "--workdir", self.wd, "--element", wid,
                                 "--reason", "client asked")
        self.assertNotEqual(code, 0)
        text = (out + err).lower()
        self.assertIn("session", text)
        self.assertIn("--force", text)

    def test_add_unknown_widget_is_refused(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--tree", "--json")
        column = [e for e in json.loads(out)["elements"] if e["elType"] == "column"][0]
        code, out, err = run_cli("add-widget", "--workdir", self.wd,
                                 "--widget", "crecs_property_fields_and_data",
                                 "--into", column["id"])
        self.assertNotEqual(code, 0)
        self.assertIn("crecs_property_fields", out + err)


class TestBinding(WorkdirCase):
    def test_bind_and_unbind_property_name(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        heading = [w for w in json.loads(out)["widgets"]
                   if w["widgetType"] == "heading"][0]
        code, out, err = run_cli("bind", "--workdir", self.wd, "--element", heading["id"],
                                 "--control", "title", "--param", "property_name")
        self.assertEqual(code, 0, out + err)
        _, detail, _ = run_cli("inspect", "--workdir", self.wd,
                               "--element", heading["id"], "--json")
        self.assertIn("__dynamic__", json.loads(detail)["settings"])
        code, out, err = run_cli("unbind", "--workdir", self.wd,
                                 "--element", heading["id"], "--control", "title")
        self.assertEqual(code, 0, out + err)

    def test_bind_rejects_an_unknown_param(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        heading = [w for w in json.loads(out)["widgets"]
                   if w["widgetType"] == "heading"][0]
        code, out, err = run_cli("bind", "--workdir", self.wd, "--element", heading["id"],
                                 "--control", "title", "--param", "size-available_sf")
        self.assertNotEqual(code, 0)
        self.assertIn("size-available_SF", out + err)


class TestValidateDiffHistory(WorkdirCase):
    def test_validate_reports_by_severity(self):
        self.init()
        code, out, _ = run_cli("validate", "--workdir", self.wd, "--json")
        payload = json.loads(out)
        for key in ("ERROR", "WARNING", "INFO"):
            self.assertIn(key, payload["counts"])
        self.assertIn(code, (0, 2))

    def test_a_complete_profile_clears_the_dependencies(self):
        self.init("--profile", PROFILE_FIXTURE)
        _, out, _ = run_cli("validate", "--workdir", self.wd, "--json")
        payload = json.loads(out)
        unresolved = [f for f in payload["findings"] if f["code"] == "E-DEP-UNRESOLVED"]
        self.assertEqual(unresolved, [], json.dumps(unresolved, indent=1)[:800])

    def test_the_shipped_example_profile_does_not_clear_the_popups(self):
        """The regression guard for D3-B2.

        Copying assets/target-profile.example.json and filling in the obvious fields
        must NOT produce a clean validation, because the template still points at the
        reference site's popups. It used to, and the result was two dead buttons.
        """
        self.init("--profile", PROFILE_EXAMPLE)
        _, out, _ = run_cli("validate", "--workdir", self.wd, "--json")
        payload = json.loads(out)
        unresolved = [f for f in payload["findings"] if f["code"] == "E-DEP-UNRESOLVED"]
        self.assertTrue(unresolved,
                        "the unedited example profile must not satisfy the popup "
                        "dependencies")
        messages = " ".join(f["message"] + " " + (f.get("hint") or "")
                            for f in unresolved)
        self.assertIn("popup --element", messages,
                      "the finding should point at the command that fixes it")

    def test_diff_shows_only_what_changed(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        wid = [w for w in json.loads(out)["widgets"]
               if w["widgetType"] == "crecs_property_fields"][0]["id"]
        run_cli("set", "--workdir", self.wd, "--element", wid,
                "--key", "card_color", "--value", "#abcdef")
        _, out, _ = run_cli("diff", "--workdir", self.wd)
        self.assertIn("card_color", out)
        self.assertIn("#abcdef", out)
        self.assertNotIn("crecs_property_docs", out)

    def test_history_then_undo(self):
        self.init()
        _, out, _ = run_cli("inspect", "--workdir", self.wd, "--widgets", "--json")
        wid = [w for w in json.loads(out)["widgets"]
               if w["widgetType"] == "crecs_property_fields"][0]["id"]
        run_cli("set", "--workdir", self.wd, "--element", wid,
                "--key", "card_color", "--value", "#111111")
        code, out, _ = run_cli("history", "--workdir", self.wd)
        self.assertEqual(code, 0)
        self.assertIn("card_color", out)
        code, out, err = run_cli("undo", "--workdir", self.wd)
        self.assertEqual(code, 0, out + err)
        _, detail, _ = run_cli("inspect", "--workdir", self.wd, "--element", wid, "--json")
        self.assertNotEqual(
            json.loads(detail)["settings"].get("card_color"), "#111111"
        )


class TestExport(WorkdirCase):
    def test_export_is_blocked_while_dependencies_are_unresolved(self):
        self.init()
        out_path = os.path.join(self.tmp, "export.json")
        code, out, err = run_cli("export", "--workdir", self.wd, "--out", out_path)
        self.assertNotEqual(code, 0)
        self.assertFalse(os.path.exists(out_path))
        self.assertIn("E-DEP-UNRESOLVED", out + err)

    def test_draft_export_is_allowed_and_marked_incomplete(self):
        self.init()
        out_path = os.path.join(self.tmp, "draft.json")
        code, out, err = run_cli("export", "--workdir", self.wd, "--out", out_path,
                                 "--allow-draft")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.exists(out_path))
        self.assertIn("draft", (out + err).lower())
        sidecar = out_path + ".report.json"
        self.assertTrue(os.path.exists(sidecar))
        self.assertFalse(json.load(open(sidecar, encoding="utf-8"))["ready"])

    def test_ready_export_with_a_profile(self):
        self.init("--profile", PROFILE_FIXTURE)
        out_path = os.path.join(self.tmp, "ready.json")
        code, out, err = run_cli("export", "--workdir", self.wd, "--out", out_path)
        self.assertEqual(code, 0, out + err)
        payload = json.load(open(out_path, encoding="utf-8"))
        self.assertIn("content", payload)
        self.assertEqual(payload["version"], "0.4")
        self.assertEqual(payload["type"], "page")

    def test_export_contains_no_internal_fields_and_no_comments(self):
        self.init("--profile", PROFILE_FIXTURE)
        out_path = os.path.join(self.tmp, "ready.json")
        run_cli("export", "--workdir", self.wd, "--out", out_path)
        raw = open(out_path, encoding="utf-8").read()
        self.assertFalse(raw.lstrip().startswith("#"))
        self.assertNotIn("//", raw.split('"content"')[0])
        payload = json.load(open(out_path, encoding="utf-8"))
        self.assertEqual(
            sorted(payload.keys()), sorted(["content", "page_settings", "title", "type", "version"])
        )

    def test_export_does_not_touch_the_working_document(self):
        self.init("--profile", PROFILE_FIXTURE)
        doc_path = os.path.join(self.wd, "document.json")
        before = open(doc_path, "rb").read()
        run_cli("export", "--workdir", self.wd,
                "--out", os.path.join(self.tmp, "x.json"))
        self.assertEqual(open(doc_path, "rb").read(), before)

    def test_applied_profile_mappings_are_recorded(self):
        self.init("--profile", PROFILE_FIXTURE)
        out_path = os.path.join(self.tmp, "ready.json")
        run_cli("export", "--workdir", self.wd, "--out", out_path)
        report = json.load(open(out_path + ".report.json", encoding="utf-8"))
        self.assertIn("applied_profile_mappings", report)


class TestCatalogCommand(unittest.TestCase):
    def test_list_widgets(self):
        code, out, _ = run_cli("catalog", "--list-widgets")
        self.assertEqual(code, 0)
        self.assertIn("crecs_property_media", out)

    def test_describe_one_widget(self):
        code, out, _ = run_cli("catalog", "--widget", "crecs_property_suites",
                               "--controls")
        self.assertEqual(code, 0)
        self.assertIn("card_body_thead_text_color", out)

    def test_unknown_widget_suggests_the_real_name(self):
        code, out, err = run_cli("catalog", "--widget", "crecs_property_fields_and_data")
        self.assertNotEqual(code, 0)
        self.assertIn("crecs_property_fields", out + err)


class TestSelftest(unittest.TestCase):
    def test_selftest_checks_package_integrity_offline(self):
        code, out, _ = run_cli("selftest")
        self.assertEqual(code, 0, out)
        self.assertIn("PASS", out)


if __name__ == "__main__":
    unittest.main()
