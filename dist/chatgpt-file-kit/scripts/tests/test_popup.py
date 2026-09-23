"""Retargeting an Elementor Pro popup — the fix for delivery-3 defect D3-B2.

D3-B2 had two halves, and both are covered here.

The template half: the shipped example profile used to declare the REFERENCE SITE's
own popup ids, 4554 and 4646. A person who copied it, filled in `site_host` and
`preview_slug` and stopped there got a clean validation and two buttons that open
nothing, because the validator cannot tell "declared because it exists here" from
"declared because I copied the example". `preview_slug` was already protected by a
placeholder the validator refuses; the popups were not. Now they are.

The skill half: there was no supported way to retarget a popup at all. `set --key
__dynamic__` is refused, correctly, and the documented remedy was "open each button in
the Elementor editor". The `popup` command closes that.
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


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class PopupCase(unittest.TestCase):
    """A workspace on the shipped base template, with a profile we control."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="crecs-popup-")
        self.workdir = os.path.join(self.tmp, "work")
        self.profile_path = os.path.join(self.tmp, "profile.json")
        self.write_profile({"4581": "Talk to an Advisor", "4584": "Contact Us"})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_profile(self, popups, **extra):
        with open(PROFILE_EXAMPLE, encoding="utf-8") as fh:
            data = json.load(fh)
        data["site_host"] = "client.test"
        data["preview_slug"] = "a-real-slug-on-this-site"
        data["popups"] = popups
        data["forbidden_literals"] = []
        data.update(extra)
        with open(self.profile_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def init(self):
        code, out, err = run_cli("init", "--from", BASE_TEMPLATE,
                                 "--workdir", self.workdir,
                                 "--profile", self.profile_path)
        self.assertEqual(code, 0, err or out)

    def popup(self, *args):
        return run_cli("popup", "--workdir", self.workdir, *args)

    def read_document(self):
        return self.read_workspace_file("document.json")

    def read_workspace_file(self, name):
        with open(os.path.join(self.workdir, name), encoding="utf-8") as fh:
            return fh.read()

    def validate_errors(self):
        code, out, err = run_cli("validate", "--workdir", self.workdir,
                                 "--level", "error", "--json")
        payload = json.loads(out) if out.strip().startswith("{") else {}
        return code, payload, out + err


class TestShippedExampleProfile(PopupCase):
    def test_the_example_profile_no_longer_declares_the_reference_sites_popups(self):
        """Copying the example and only filling in the obvious fields must not pass."""
        with open(PROFILE_EXAMPLE, encoding="utf-8") as fh:
            declared = list((json.load(fh).get("popups") or {}).keys())
        for source_id in ("4554", "4646"):
            self.assertNotIn(
                source_id, declared,
                "the example profile must not pre-declare the reference site's popup "
                "id %s: it makes validation pass while the button opens nothing"
                % source_id,
            )

    def test_the_example_profiles_popup_keys_look_like_placeholders(self):
        with open(PROFILE_EXAMPLE, encoding="utf-8") as fh:
            declared = list((json.load(fh).get("popups") or {}).keys())
        self.assertTrue(declared, "the example should still show the shape of the map")
        for key in declared:
            self.assertFalse(
                key.isdigit(),
                "a numeric key in the example is indistinguishable from a real id: %r" % key,
            )

    def test_the_unedited_example_profile_blocks_an_export(self):
        self.profile_path = PROFILE_EXAMPLE
        code, out, err = run_cli("init", "--from", BASE_TEMPLATE,
                                 "--workdir", self.workdir,
                                 "--profile", PROFILE_EXAMPLE)
        self.assertEqual(code, 0, err or out)
        code, _, text = self.validate_errors()
        self.assertEqual(code, 2, "an unedited example profile must not validate clean")
        self.assertIn("popup", text.lower())


class TestPopupList(PopupCase):
    def test_list_reports_every_popup_binding(self):
        self.init()
        code, out, err = self.popup("--list", "--json")
        self.assertEqual(code, 0, err or out)
        payload = json.loads(out)
        self.assertEqual(len(payload["bindings"]), 2,
                         "the base template has two contact buttons")
        for binding in payload["bindings"]:
            for key in ("element_id", "control", "popup_id", "declared_by_profile"):
                self.assertIn(key, binding)
        self.assertEqual({b["popup_id"] for b in payload["bindings"]}, {"4554", "4646"})
        self.assertTrue(all(b["declared_by_profile"] is False
                            for b in payload["bindings"]),
                        "this profile declares 4581/4584, not the template's ids")

    def test_list_does_not_need_a_reason_or_change_anything(self):
        self.init()
        before = self.read_document()
        self.popup("--list")
        after = self.read_document()
        self.assertEqual(before, after, "--list must be read-only")


class TestPopupSet(PopupCase):
    def test_retargeting_to_a_declared_popup_succeeds(self):
        self.init()
        code, out, _ = self.popup("--list", "--json")
        first = json.loads(out)["bindings"][0]

        code, out, err = self.popup("--element", first["element_id"],
                                    "--control", first["control"],
                                    "--set", "4581",
                                    "--decision", "Client's own advisor popup.")
        self.assertEqual(code, 0, err or out)

        code, out, _ = self.popup("--list", "--json")
        after = {b["element_id"]: b for b in json.loads(out)["bindings"]}
        self.assertEqual(after[first["element_id"]]["popup_id"], "4581")
        self.assertTrue(after[first["element_id"]]["declared_by_profile"])

    def test_retargeting_records_the_decision(self):
        self.init()
        code, out, _ = self.popup("--list", "--json")
        first = json.loads(out)["bindings"][0]
        self.popup("--element", first["element_id"], "--control", first["control"],
                   "--set", "4581", "--decision", "Acme picked their advisor popup.")
        decisions = self.read_workspace_file("decisions.md")
        self.assertIn("Acme picked their advisor popup.", decisions)

    def test_an_id_the_profile_does_not_declare_is_refused(self):
        self.init()
        code, out, _ = self.popup("--list", "--json")
        first = json.loads(out)["bindings"][0]
        before = self.read_document()

        code, out, err = self.popup("--element", first["element_id"],
                                    "--control", first["control"],
                                    "--set", "9999",
                                    "--decision", "guessing")
        self.assertNotEqual(code, 0, "an undeclared id must be refused")
        text = (out + err).lower()
        self.assertIn("9999", out + err)
        self.assertIn("profile", text)
        after = self.read_document()
        self.assertEqual(before, after, "nothing may be written on a refusal")

    def test_an_element_with_no_popup_binding_is_refused_by_name(self):
        self.init()
        code, out, err = self.popup("--element", "b133d6f", "--control", "link",
                                    "--set", "4581", "--decision", "x")
        self.assertNotEqual(code, 0)
        self.assertIn("b133d6f", out + err)

    def test_set_requires_a_decision(self):
        self.init()
        code, out, _ = self.popup("--list", "--json")
        first = json.loads(out)["bindings"][0]
        code, out, err = self.popup("--element", first["element_id"],
                                    "--control", first["control"], "--set", "4581")
        self.assertNotEqual(code, 0, "a write must be accountable")


class TestPopupClear(PopupCase):
    def test_clear_removes_the_binding_and_needs_a_reason(self):
        self.init()
        code, out, _ = self.popup("--list", "--json")
        first = json.loads(out)["bindings"][0]

        code, out, err = self.popup("--element", first["element_id"],
                                    "--control", first["control"], "--clear")
        self.assertNotEqual(code, 0, "clearing a binding must state why")

        code, out, err = self.popup("--element", first["element_id"],
                                    "--control", first["control"], "--clear",
                                    "--decision", "This client has no advisor popup.")
        self.assertEqual(code, 0, err or out)

        code, out, _ = self.popup("--list", "--json")
        remaining = json.loads(out)["bindings"]
        self.assertEqual(len(remaining), 1, "one binding should be gone")


class TestD3B2Acceptance(PopupCase):
    """The end state D3-B2 asks for: the shipped template can be made exportable."""

    def test_retargeting_both_buttons_clears_the_export_gate(self):
        self.init()
        code, payload, text = self.validate_errors()
        self.assertEqual(code, 2, "as shipped, against a real profile, export is blocked")

        code, out, _ = self.popup("--list", "--json")
        bindings = json.loads(out)["bindings"]
        for binding, target in zip(bindings, ("4581", "4584")):
            code, out, err = self.popup("--element", binding["element_id"],
                                        "--control", binding["control"],
                                        "--set", target,
                                        "--decision", "Retargeted for this client.")
            self.assertEqual(code, 0, err or out)

        code, payload, text = self.validate_errors()
        self.assertEqual(code, 0, "after retargeting, nothing should block the export:\n" + text)

    def test_export_succeeds_after_retargeting(self):
        self.init()
        code, out, _ = self.popup("--list", "--json")
        for binding, target in zip(json.loads(out)["bindings"], ("4581", "4584")):
            self.popup("--element", binding["element_id"], "--control", binding["control"],
                       "--set", target, "--decision", "Retargeted.")
        out_path = os.path.join(self.tmp, "export.json")
        code, out, err = run_cli("export", "--workdir", self.workdir, "--out", out_path)
        self.assertEqual(code, 0, err or out)
        self.assertTrue(os.path.isfile(out_path))
        with open(out_path, encoding="utf-8") as fh:
            exported = json.dumps(json.load(fh))
        self.assertIn("4581", exported)
        self.assertIn("4584", exported)
        self.assertNotIn("%224554%22", exported)


class TestTheHintDoesNotTeachTheTrap(PopupCase):
    def test_the_unresolved_hint_does_not_suggest_declaring_the_source_id(self):
        """The old hint said: add "4554" to your profile. That is the trap itself."""
        self.init()
        code, out, err = run_cli("validate", "--workdir", self.workdir, "--level", "error")
        text = out + err
        self.assertIn("E-DEP-UNRESOLVED", text)
        self.assertNotIn('Add "4554"', text)
        self.assertNotIn('Add "4646"', text)
        self.assertIn("popup --element", text,
                      "the hint should point at the command that fixes it")
        self.assertIn("--set", text)
        self.assertIn("would silence this check", text,
                      "the hint should say why declaring the source id is wrong")


class TestPopupInTheCli(PopupCase):
    def test_popup_is_listed_in_top_level_help(self):
        code, out, _ = run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("popup", out)

    def test_popup_has_its_own_help(self):
        code, out, _ = run_cli("popup", "--help")
        self.assertEqual(code, 0)
        for flag in ("--list", "--set", "--clear", "--element", "--control"):
            self.assertIn(flag, out)
