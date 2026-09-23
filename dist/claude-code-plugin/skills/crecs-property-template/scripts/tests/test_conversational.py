"""The twelve conversational scenarios from the brief, as scripted command
sequences with asserted outcomes.

Each scenario is what a request in chat turns into. Passing here means "tested in the
harness" — it does not mean the result was rendered or imported into Elementor.
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
BASE = os.path.join(SKILL_ROOT, "assets", "property-template-all-widgets.json")
# A profile that is complete for the shipped template. The shipped EXAMPLE is not, on
# purpose: it no longer declares the reference site's popup ids, because a copied
# profile that did let the template validate clean with two dead buttons — delivery-3
# defect D3-B2. See scripts/tests/fixtures/target-profile.test.json.
PROFILE = os.path.join(HERE, "fixtures", "target-profile.test.json")


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class Scenario(unittest.TestCase):
    """One workspace per scenario, built from the shipped base template."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")
        code, out, err = run("init", "--from", BASE, "--workdir", self.wd,
                             "--profile", PROFILE)
        self.assertEqual(code, 0, out + err)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # -- helpers ---------------------------------------------------------------

    def widgets(self):
        _, out, _ = run("inspect", "--workdir", self.wd, "--widgets", "--json")
        return json.loads(out)["widgets"]

    def wid(self, widget_type, index=0):
        found = [w for w in self.widgets() if w["widgetType"] == widget_type]
        self.assertTrue(found, "widget absent from the base template: " + widget_type)
        return found[index]["id"]

    def settings(self, element_id):
        _, out, _ = run("inspect", "--workdir", self.wd, "--element", element_id, "--json")
        return json.loads(out)["settings"]

    def document(self):
        with open(os.path.join(self.wd, "document.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def assert_clean(self):
        code, out, _ = run("validate", "--workdir", self.wd, "--json")
        payload = json.loads(out)
        self.assertEqual(payload["counts"]["ERROR"], 0,
                         json.dumps([f for f in payload["findings"]
                                     if f["severity"] == "ERROR"], indent=1)[:1200])
        return payload


class S01ChangeOneColour(Scenario):
    """"Make the field card background white." Nothing else may move."""

    def test_only_that_one_key_changes(self):
        wid = self.wid("crecs_property_fields")
        before = json.dumps(self.document(), sort_keys=True)
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "card_color", "--value", "#FFFFFF")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.settings(wid)["card_color"], "#FFFFFF")
        _, diff, _ = run("diff", "--workdir", self.wd)
        self.assertIn("card_color", diff)
        self.assertEqual(len([ln for ln in diff.splitlines() if ln.startswith("~")]), 1,
                         diff)
        after = json.loads(json.dumps(self.document()))
        self.assertNotEqual(before, json.dumps(after, sort_keys=True))
        self.assert_clean()


class S02ReorganiseGalleryAndDetails(Scenario):
    """"Put the details block above the media box." Ids must survive the move."""

    def test_move_preserves_ids_and_bindings(self):
        media = self.wid("crecs_property_media")
        details = self.wid("crecs_property_details")
        code, out, err = run("move", "--workdir", self.wd, "--element", details,
                             "--before", media)
        self.assertEqual(code, 0, out + err)
        order = [w["id"] for w in self.widgets()]
        self.assertLess(order.index(details), order.index(media))
        self.assertEqual(self.wid("crecs_property_details"), details)
        self.assert_clean()

    def test_the_loader_stays_first_after_reordering(self):
        media = self.wid("crecs_property_media")
        run("move", "--workdir", self.wd, "--element", media, "--before",
            self.wid("crecs_property_fields"))
        self.assertEqual(self.widgets()[0]["widgetType"], "crecs_property_data")


class S03MobileWithoutTouchingDesktop(Scenario):
    """"Tighten the card padding on mobile only.\""""

    def test_desktop_value_is_untouched(self):
        wid = self.wid("crecs_property_fields")
        desktop_before = self.settings(wid).get("card_padding")
        value = json.dumps({"unit": "px", "top": "6", "right": "6", "bottom": "6",
                            "left": "6", "isLinked": True})
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "card_padding", "--device", "mobile",
                             "--value", value)
        self.assertEqual(code, 0, out + err)
        now = self.settings(wid)
        self.assertEqual(now.get("card_padding"), desktop_before)
        self.assertEqual(now["card_padding_mobile"]["top"], "6")
        self.assert_clean()

    def test_a_device_variant_of_a_flat_control_is_refused_with_the_reason(self):
        wid = self.wid("crecs_property_fields")
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "card_color", "--device", "tablet",
                             "--value", "#eeeeee")
        self.assertNotEqual(code, 0)
        self.assertIn("is_responsive", (out + err))


class S04TypographyAndHover(Scenario):
    """"Make the suite attachment links bolder and change their hover colour.\""""

    def test_typography_and_hover_are_both_reachable(self):
        wid = self.wid("crecs_property_suites")
        steps = [
            ("attachment_link_typography_typography", "custom", None),
            ("attachment_link_typography_font_weight", "700", None),
            ("attachment_link_text_color_hover", "#3B82F6", None),
            ("attachment_link_typography_font_size", json.dumps(
                {"unit": "px", "size": 15, "sizes": []}), "tablet"),
        ]
        for key, value, device in steps:
            args = ["set", "--workdir", self.wd, "--element", wid,
                    "--key", key, "--value", value]
            if device:
                args += ["--device", device]
            code, out, err = run(*args)
            self.assertEqual(code, 0, key + ": " + out + err)
        now = self.settings(wid)
        self.assertEqual(now["attachment_link_typography_font_weight"], "700",
                         "the CLI must store a font weight as the string Elementor "
                         "compares against, not as a number")
        self.assertEqual(now["attachment_link_text_color_hover"], "#3B82F6")
        self.assertIn("attachment_link_typography_font_size_tablet", now)
        self.assert_clean()

    def test_the_attachments_widget_uses_a_different_vocabulary(self):
        """attachment_link_* exists on suites and not on attachments. The tool must
        refuse rather than silently write a dead key."""
        wid = self.wid("crecs_property_attachments")
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "attachment_link_text_color", "--value", "#123456")
        self.assertNotEqual(code, 0)
        self.assertIn("card_body_color", out + err)


class S05AddMissingWidget(Scenario):
    """"We also want the traffic counts." (Already present; add a second attachments
    card to prove the path.)"""

    def test_add_a_widget_into_a_column(self):
        _, out, _ = run("inspect", "--workdir", self.wd, "--tree", "--json")
        columns = [e for e in json.loads(out)["elements"] if e["elType"] == "column"]
        target = columns[-1]["id"]
        code, out, err = run("add-widget", "--workdir", self.wd,
                             "--widget", "crecs_property_attachments",
                             "--into", target)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(
            len([w for w in self.widgets() if w["widgetType"] == "crecs_property_attachments"]),
            2,
        )
        self.assert_clean()

    def test_adding_a_second_map_is_refused_with_the_technical_reason(self):
        _, out, _ = run("inspect", "--workdir", self.wd, "--tree", "--json")
        target = [e for e in json.loads(out)["elements"]
                  if e["elType"] == "column"][-1]["id"]
        code, out, err = run("add-widget", "--workdir", self.wd,
                             "--widget", "crecs_property_map", "--into", target)
        self.assertNotEqual(code, 0)
        self.assertIn("crecs_map_widget_plot_pov", out + err)


class S06RemoveSectionExplicitly(Scenario):
    """"Drop the demographics card, this client never fills it in.\""""

    def test_removal_is_recorded_with_its_reason(self):
        wid = self.wid("crecs_property_demographic")
        code, out, err = run("remove", "--workdir", self.wd, "--element", wid,
                             "--reason", "client does not populate demographics")
        self.assertEqual(code, 0, out + err)
        self.assertEqual(
            [w for w in self.widgets() if w["widgetType"] == "crecs_property_demographic"],
            [],
        )
        decisions = open(os.path.join(self.wd, "decisions.md"), encoding="utf-8").read()
        self.assertIn("client does not populate demographics", decisions)

    def test_the_catalog_still_supports_the_removed_widget(self):
        wid = self.wid("crecs_property_demographic")
        run("remove", "--workdir", self.wd, "--element", wid, "--reason", "not used")
        code, out, _ = run("catalog", "--widget", "crecs_property_demographic", "--controls")
        self.assertEqual(code, 0)
        self.assertIn("table_body_color", out)

    def test_removal_without_a_reason_is_refused(self):
        wid = self.wid("crecs_property_demographic")
        code, out, err = run("remove", "--workdir", self.wd, "--element", wid)
        self.assertNotEqual(code, 0)
        self.assertIn("--reason", out + err)

    def test_removing_a_functionally_required_widget_needs_force_and_an_alternative(self):
        wid = self.wid("crecs_property_data")
        code, out, err = run("remove", "--workdir", self.wd, "--element", wid,
                             "--reason", "client asked")
        self.assertNotEqual(code, 0)
        text = (out + err).lower()
        self.assertIn("session", text)
        self.assertIn("--force", text)


class S07KeepPropertyNameBinding(Scenario):
    def test_the_binding_survives_edits_and_moves(self):
        bound = None
        for widget in self.widgets():
            dyn = self.settings(widget["id"]).get("__dynamic__") or {}
            for control, shortcode in dyn.items():
                if "property_name" in shortcode:
                    bound = (widget["id"], control)
        self.assertIsNotNone(bound, "the base template must bind property_name")
        wid, control = bound
        run("set", "--workdir", self.wd, "--element", wid, "--key", "align",
            "--value", "center")
        run("move", "--workdir", self.wd, "--element", wid, "--after",
            self.wid("crecs_property_data"))
        dyn = self.settings(wid)["__dynamic__"]
        self.assertIn(control, dyn)
        self.assertIn("property_name", dyn[control])
        payload = self.assert_clean()
        self.assertIn("property_name", payload["summary"]["bound_params"])

    def test_unbinding_is_explicit(self):
        heading = [w for w in self.widgets() if w["widgetType"] == "heading"][0]["id"]
        dyn = self.settings(heading).get("__dynamic__") or {}
        if dyn:
            control = sorted(dyn)[0]
            code, out, err = run("unbind", "--workdir", self.wd, "--element", heading,
                                 "--control", control)
            self.assertEqual(code, 0, out + err)
            self.assertNotIn(control, self.settings(heading).get("__dynamic__") or {})


class S08PreserveUnknownFields(Scenario):
    def test_third_party_keys_survive_a_full_edit_cycle(self):
        wid = self.wid("crecs_property_fields")
        before = self.settings(wid)
        preexisting = {k: v for k, v in before.items()
                       if k.startswith(("pa_", "premium_"))}
        self.assertTrue(preexisting, "the base template should carry PAE defaults")
        run("set", "--workdir", self.wd, "--element", wid,
            "--key", "card_color", "--value", "#fafafa")
        after = self.settings(wid)
        for key, value in preexisting.items():
            self.assertEqual(after[key], value, key)

    def test_an_unknown_key_present_at_import_is_flagged_not_deleted(self):
        doc_path = os.path.join(self.wd, "document.json")
        payload = json.load(open(doc_path, encoding="utf-8"))
        payload["content"][0]["settings"]["some_legacy_addon_key"] = {"id": "1", "url": "x"}
        with open(doc_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        run("init", "--from", doc_path, "--workdir", self.wd + "2", "--profile", PROFILE)
        _, out, _ = run("validate", "--workdir", self.wd + "2", "--json")
        result = json.loads(out)
        codes = [f["code"] for f in result["findings"]]
        self.assertIn("W-KEY-PREEXISTING-UNKNOWN", codes)
        self.assertNotIn("E-CONTROL-UNKNOWN", codes)
        doc2 = json.load(open(os.path.join(self.wd + "2", "document.json"),
                              encoding="utf-8"))
        self.assertIn("some_legacy_addon_key", doc2["content"][0]["settings"])


class S09RejectNonexistentControl(Scenario):
    def test_an_invented_key_is_refused_and_nothing_is_written(self):
        wid = self.wid("crecs_property_fields")
        before = json.dumps(self.document(), sort_keys=True)
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "card_neon_glow", "--value", "10")
        self.assertNotEqual(code, 0)
        self.assertEqual(json.dumps(self.document(), sort_keys=True), before)

    def test_a_legacy_alias_is_refused_with_the_current_name(self):
        wid = self.wid("crecs_property_fields")
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "label_typography_font_size",
                             "--value", json.dumps({"unit": "px", "size": 16, "sizes": []}))
        self.assertNotEqual(code, 0)
        self.assertIn("field_label_typography_font_size", out + err)


class S10Undo(Scenario):
    def test_undo_restores_the_previous_content(self):
        wid = self.wid("crecs_property_fields")
        original = self.settings(wid).get("card_color")
        run("set", "--workdir", self.wd, "--element", wid,
            "--key", "card_color", "--value", "#0F0F0F")
        self.assertEqual(self.settings(wid)["card_color"], "#0F0F0F")
        code, out, err = run("undo", "--workdir", self.wd)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(self.settings(wid).get("card_color"), original)

    def test_undo_of_a_removal_brings_the_widget_back(self):
        wid = self.wid("crecs_property_traffic")
        run("remove", "--workdir", self.wd, "--element", wid, "--reason", "test")
        self.assertEqual(
            [w for w in self.widgets() if w["widgetType"] == "crecs_property_traffic"], []
        )
        run("undo", "--workdir", self.wd)
        back = [w for w in self.widgets() if w["widgetType"] == "crecs_property_traffic"]
        self.assertEqual(len(back), 1)
        self.assertEqual(back[0]["id"], wid)


class S11ResumeElsewhere(Scenario):
    def test_a_new_process_continues_from_the_recorded_state(self):
        wid = self.wid("crecs_property_fields")
        run("set", "--workdir", self.wd, "--element", wid,
            "--key", "card_color", "--value", "#223344")
        code, out, _ = run("history", "--workdir", self.wd, "--json")
        self.assertEqual(code, 0)
        state = json.loads(out)
        self.assertGreaterEqual(state["revision"], 1)
        self.assertIn("document_sha256", state)
        # A completely fresh invocation, as another session would do.
        _, again, _ = run("inspect", "--workdir", self.wd, "--element", wid, "--json")
        self.assertEqual(json.loads(again)["settings"]["card_color"], "#223344")

    def test_an_external_edit_is_detected_rather_than_overwritten(self):
        wid = self.wid("crecs_property_fields")
        doc_path = os.path.join(self.wd, "document.json")
        payload = json.load(open(doc_path, encoding="utf-8"))
        payload["title"] = "Edited outside the tool"
        with open(doc_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "card_color", "--value", "#556677")
        self.assertNotEqual(code, 0)
        self.assertIn("external", (out + err).lower())
        self.assertEqual(json.load(open(doc_path, encoding="utf-8"))["title"],
                         "Edited outside the tool")

    def test_accept_external_then_continue(self):
        wid = self.wid("crecs_property_fields")
        doc_path = os.path.join(self.wd, "document.json")
        payload = json.load(open(doc_path, encoding="utf-8"))
        payload["title"] = "Edited outside the tool"
        with open(doc_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        code, out, err = run("set", "--workdir", self.wd, "--element", wid,
                             "--key", "card_color", "--value", "#556677",
                             "--accept-external")
        self.assertEqual(code, 0, out + err)


class S12Export(Scenario):
    def test_ready_export_round_trips(self):
        out_path = os.path.join(self.tmp, "property-page.json")
        code, out, err = run("export", "--workdir", self.wd, "--out", out_path)
        self.assertEqual(code, 0, out + err)
        payload = json.load(open(out_path, encoding="utf-8"))
        self.assertEqual(payload["version"], "0.4")
        self.assertTrue(payload["content"])
        report = json.load(open(out_path + ".report.json", encoding="utf-8"))
        self.assertTrue(report["ready"])
        self.assertEqual(report["counts"]["ERROR"], 0)

    def test_an_export_can_be_reimported_and_validates_the_same(self):
        out_path = os.path.join(self.tmp, "property-page.json")
        run("export", "--workdir", self.wd, "--out", out_path)
        second = os.path.join(self.tmp, "work2")
        code, out, err = run("init", "--from", out_path, "--workdir", second,
                             "--profile", PROFILE)
        self.assertEqual(code, 0, out + err)
        _, res, _ = run("validate", "--workdir", second, "--json")
        self.assertEqual(json.loads(res)["counts"]["ERROR"], 0)

    def test_a_blocked_export_names_the_blocking_findings(self):
        wid = self.wid("crecs_property_fields")
        doc_path = os.path.join(self.wd, "document.json")
        payload = json.load(open(doc_path, encoding="utf-8"))

        def poison(node):
            if node.get("id") == wid:
                node["settings"]["card_glow"] = 1
            for child in node.get("elements", []) or []:
                poison(child)

        for root in payload["content"]:
            poison(root)
        with open(doc_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        out_path = os.path.join(self.tmp, "blocked.json")
        code, out, err = run("export", "--workdir", self.wd, "--out", out_path,
                             "--accept-external")
        self.assertNotEqual(code, 0)
        self.assertIn("E-CONTROL-UNKNOWN", out + err)
        self.assertFalse(os.path.exists(out_path))


if __name__ == "__main__":
    unittest.main()
