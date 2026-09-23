"""F7: the skill must be able to say what a document already binds.

`bind` and `unbind` write a binding; `popup --list` reads back popup bindings only.
Nothing could answer "what is bound here, and to what" — so during a client session the
question was answered by reading the exported JSON with a throwaway script.

The question mattered. Eight headings carried Elementor's placeholder text, "Add Your
Heading Text Here", and looked like leftovers. Seven of them were bound to
`property_name`, the street address, the city line, `property_type`, `property_category`,
`property_headline` and `property_description`: deleting them would have stripped the
name, address, type and description from every property on the site at once. The eighth
was bound to the map zoom level and really was dead weight.

A decision about whether a deletion is safe should not depend on someone writing a
script correctly under time pressure.
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
PROFILE = os.path.join(HERE, "fixtures", "target-profile.test.json")


def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class BindListing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")
        code, out, err = run("init", "--from", BASE, "--workdir", self.wd,
                             "--profile", PROFILE)
        self.assertEqual(code, 0, out + err)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def listing(self):
        code, out, err = run("bind", "--list", "--workdir", self.wd, "--json")
        self.assertEqual(code, 0, out + err)
        return json.loads(out)

    def test_bind_list_runs_without_the_writing_arguments(self):
        # --element/--control/--param are required to WRITE a binding; asking what
        # exists must not require naming one.
        code, out, err = run("bind", "--list", "--workdir", self.wd)
        self.assertEqual(code, 0, out + err)

    def test_it_reports_the_property_bindings_in_the_shipped_template(self):
        found = self.listing()["bindings"]
        self.assertTrue(found, "the base template binds fields; none were reported")
        params = {b["param"] for b in found if b.get("tag") == "crecs-property"}
        self.assertIn("property_name", params)

    def test_every_row_says_element_control_and_param(self):
        for b in self.listing()["bindings"]:
            for key in ("element_id", "element_type", "control", "tag"):
                self.assertIn(key, b)

    def test_it_reports_the_fallback_text_so_a_placeholder_is_recognisable(self):
        # This is the whole point: a heading reading "Add Your Heading Text Here" is
        # not a leftover if a binding replaces it at render time. Showing the stored
        # value next to the binding is what makes that visible.
        rows = [b for b in self.listing()["bindings"]
                if b.get("control") == "title" and b.get("tag") == "crecs-property"]
        self.assertTrue(rows, "no bound headings found in the base template")
        self.assertIn("stored_value", rows[0])

    def test_popup_bindings_appear_too(self):
        # popup --list stays, but the general listing must not pretend popups are not
        # bindings; leaving them out is how someone concludes a button is unbound.
        tags = {b.get("tag") for b in self.listing()["bindings"]}
        self.assertIn("popup", tags)

    def test_it_can_be_narrowed_to_one_element(self):
        all_rows = self.listing()["bindings"]
        target = all_rows[0]["element_id"]
        code, out, _ = run("bind", "--list", "--element", target,
                           "--workdir", self.wd, "--json")
        self.assertEqual(code, 0)
        rows = json.loads(out)["bindings"]
        self.assertTrue(rows)
        self.assertEqual({target}, {r["element_id"] for r in rows})

    def test_a_broken_binding_is_reported_rather_than_hidden(self):
        doc_path = os.path.join(self.wd, "document.json")
        with open(doc_path, encoding="utf-8") as fh:
            doc = json.load(fh)

        def first_widget(nodes):
            for n in nodes:
                if n.get("elType") == "widget":
                    return n
                found = first_widget(n.get("elements", []))
                if found:
                    return found
            return None

        content = doc["content"] if isinstance(doc, dict) else doc
        w = first_widget(content)
        w.setdefault("settings", {}).setdefault("__dynamic__", {})["title"] = "not a tag"
        with open(doc_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)

        code, out, err = run("bind", "--list", "--workdir", self.wd, "--json",
                             "--accept-external")
        self.assertEqual(code, 0, out + err)
        rows = json.loads(out)["bindings"]
        broken = [r for r in rows if r.get("error")]
        self.assertTrue(broken, "a malformed tag must be listed with its error, not dropped")

    def test_the_text_output_names_the_field_not_just_the_control(self):
        _, out, _ = run("bind", "--list", "--workdir", self.wd)
        self.assertIn("property_name", out)

    def test_the_listing_does_not_change_the_document(self):
        doc_path = os.path.join(self.wd, "document.json")
        with open(doc_path, "rb") as fh:
            before = fh.read()
        run("bind", "--list", "--workdir", self.wd)
        with open(doc_path, "rb") as fh:
            self.assertEqual(before, fh.read())


class SkillDocumentsIt(unittest.TestCase):
    def test_skill_md_mentions_bind_list(self):
        with open(os.path.join(SKILL_ROOT, "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("bind --list", text)

    def test_skill_md_warns_before_deleting_something_that_looks_empty(self):
        with open(os.path.join(SKILL_ROOT, "SKILL.md"), encoding="utf-8") as fh:
            lowered = fh.read().lower()
        self.assertTrue(
            "placeholder" in lowered and "bind --list" in lowered,
            "SKILL.md does not tell the assistant to check bindings before removing "
            "something that looks like placeholder text",
        )


if __name__ == "__main__":
    unittest.main()
