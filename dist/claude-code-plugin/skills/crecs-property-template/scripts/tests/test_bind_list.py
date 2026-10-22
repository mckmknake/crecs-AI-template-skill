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
import re
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


LOGO_SHORTCODE = re.compile(
    r'^\[elementor-tag id="[0-9a-f]{7}" name="(crecs-company-logo|crecs-flyer-logo)" settings="%7B%7D"\]$')


class BindingTheClientsLogo(unittest.TestCase):
    """The client's company logo and flyer logo are tags with no settings, bound to an
    image widget's picture. The whole path: an image widget in, a tag on its picture, the
    binding kept through validate and export, and everything wrong refused before it is
    written."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")
        code, out, err = run("init", "--from", BASE, "--workdir", self.wd, "--profile", PROFILE)
        self.assertEqual(code, 0, out + err)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def document_bytes(self):
        with open(os.path.join(self.wd, "document.json"), "rb") as fh:
            return fh.read()

    def document(self):
        return json.loads(self.document_bytes().decode("utf-8"))

    def walk(self, nodes):
        for node in nodes:
            yield node
            for inner in self.walk(node.get("elements", [])):
                yield inner

    def roots(self):
        doc = self.document()
        return doc["content"] if isinstance(doc, dict) else doc

    def a_column(self):
        return next(n["id"] for n in self.walk(self.roots()) if n.get("elType") == "column")

    def element(self, element_id):
        return next(n for n in self.walk(self.roots()) if n.get("id") == element_id)

    def a_heading(self):
        code, out, err = run("inspect", "--workdir", self.wd, "--widgets", "--json")
        self.assertEqual(code, 0, out + err)
        return next(w["id"] for w in json.loads(out)["widgets"] if w["widgetType"] == "heading")

    def add_image(self):
        code, out, err = run("add-widget", "--widget", "image", "--into", self.a_column(),
                             "--workdir", self.wd, "--json", "--decision", "A place for the logo.")
        self.assertEqual(code, 0, out + err)
        return json.loads(out)

    def bind(self, element, *extra):
        return run("bind", "--element", element, "--workdir", self.wd, "--json", *extra)

    # -- getting an image widget in ---------------------------------------------------------

    def test_an_image_widget_goes_into_a_column_and_its_reference_is_a_real_file(self):
        added = self.add_image()
        self.assertEqual("image", added["widgetType"])
        self.assertEqual("image", self.element(added["element_id"])["widgetType"])
        self.assertTrue(os.path.isfile(os.path.join(SKILL_ROOT, added["reference"])),
                        "add-widget names a reference file that is not there: %s" % added["reference"])

    def test_inspect_and_catalog_name_real_reference_files_for_core_widgets_too(self):
        added = self.add_image()
        code, out, err = run("inspect", "--workdir", self.wd, "--element", added["element_id"], "--json")
        self.assertEqual(code, 0, out + err)
        reference = json.loads(out)["catalog"]["reference"]
        self.assertTrue(os.path.isfile(os.path.join(SKILL_ROOT, reference)), reference)
        code, out, err = run("catalog", "--widget", "image", "--json")
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(SKILL_ROOT, json.loads(out)["reference"])))

    # -- writing the binding ---------------------------------------------------------------------

    def test_a_logo_tag_is_bound_to_the_picture_with_no_param_in_the_saved_form_elementor_needs(self):
        for tag in ("crecs-company-logo", "crecs-flyer-logo"):
            with self.subTest(tag=tag):
                image = self.add_image()["element_id"]
                code, out, err = self.bind(image, "--control", "image", "--tag", tag,
                                           "--decision", "The logo follows CRE Cloud.")
                self.assertEqual(0, code, out + err)
                payload = json.loads(out)
                self.assertEqual(tag, payload["tag"])
                self.assertRegex(payload["shortcode"], LOGO_SHORTCODE)
                self.assertIn('name="%s"' % tag, payload["shortcode"])
                saved = self.element(image)["settings"]["__dynamic__"]
                self.assertEqual({"image": payload["shortcode"]}, saved)

    def test_the_bound_widget_passes_validate_and_survives_export(self):
        image = self.add_image()["element_id"]
        code, out, err = self.bind(image, "--control", "image", "--tag", "crecs-company-logo")
        self.assertEqual(0, code, out + err)
        shortcode = json.loads(out)["shortcode"]

        code, out, err = run("validate", "--workdir", self.wd, "--json")
        self.assertEqual(0, code, out + err)
        mine = [f for f in json.loads(out)["findings"] if f.get("element_id") == image]
        self.assertEqual([], [f for f in mine if f["severity"] != "INFO"], mine)
        self.assertNotIn("I-BINDING-OTHER-TAG", [f["code"] for f in mine],
                         "the logo tag is registered: it must not be waved through as unknown")

        exported = os.path.join(self.tmp, "page.json")
        code, out, err = run("export", "--workdir", self.wd, "--out", exported)
        self.assertEqual(0, code, out + err)
        with open(exported, encoding="utf-8") as fh:
            envelope = json.load(fh)
        content = envelope["content"] if isinstance(envelope, dict) else envelope
        bound = [n for n in self.walk(content) if n.get("widgetType") == "image"
                 and n.get("settings", {}).get("__dynamic__", {}).get("image") == shortcode]
        self.assertEqual(1, len(bound), "the exported page lost the bound logo")

    def test_a_tag_that_does_not_exist_is_refused_and_nothing_is_written(self):
        image = self.add_image()["element_id"]
        before = self.document_bytes()
        for typo in ("crecs-company-logos", "crecs_company_logo", "company-logo"):
            with self.subTest(tag=typo):
                code, out, err = self.bind(image, "--control", "image", "--tag", typo)
                self.assertEqual(1, code, out)
                self.assertIn("crecs-company-logo", err, "it does not say which tag was meant")
                self.assertEqual(before, self.document_bytes())

    def test_a_control_of_the_wrong_kind_is_refused_and_nothing_is_written(self):
        image = self.add_image()["element_id"]
        before = self.document_bytes()
        code, out, err = self.bind(image, "--control", "caption", "--tag", "crecs-company-logo")
        self.assertEqual(1, code, out)
        self.assertIn("E-BINDING-CATEGORY", err)
        self.assertEqual(before, self.document_bytes())
        code, out, err = self.bind(self.a_heading(), "--control", "title", "--tag", "crecs-flyer-logo")
        self.assertEqual(1, code, out)
        self.assertIn("E-BINDING-CATEGORY", err)
        self.assertEqual(before, self.document_bytes())
        # A control that takes no tag at all would only get a binding that does nothing.
        code, out, err = self.bind(image, "--control", "image_size", "--tag", "crecs-company-logo")
        self.assertEqual(1, code, out)
        self.assertIn("takes a dynamic tag", err)
        self.assertEqual(before, self.document_bytes())

    def test_a_control_the_widget_does_not_have_is_refused(self):
        image = self.add_image()["element_id"]
        before = self.document_bytes()
        code, out, err = self.bind(image, "--control", "picture", "--tag", "crecs-company-logo")
        self.assertEqual(1, code, out)
        self.assertIn("no control", err)
        self.assertEqual(before, self.document_bytes())

    def test_a_param_is_refused_for_a_tag_that_takes_none(self):
        image = self.add_image()["element_id"]
        before = self.document_bytes()
        code, out, err = self.bind(image, "--control", "image", "--tag", "crecs-company-logo",
                                   "--param", "property_name")
        self.assertEqual(1, code, out)
        self.assertIn("takes no", err)
        self.assertEqual(before, self.document_bytes())

    def test_the_property_tag_still_needs_its_param(self):
        code, out, err = self.bind(self.a_heading(), "--control", "title")
        self.assertEqual(1, code, out)
        self.assertIn("--param", err)

    def test_the_forbidden_tag_and_the_popup_tag_are_not_written_by_bind(self):
        image = self.add_image()["element_id"]
        before = self.document_bytes()
        code, _out, err = self.bind(image, "--control", "image", "--tag", "crecs-test")
        self.assertEqual(1, code)
        self.assertIn("crecs-test", err)
        code, _out, err = self.bind(image, "--control", "link", "--tag", "popup")
        self.assertEqual(1, code)
        self.assertIn("popup --element", err, "it does not point at the command that writes popup bindings")
        self.assertEqual(before, self.document_bytes())

    def test_the_binding_can_be_taken_off_again(self):
        image = self.add_image()["element_id"]
        self.bind(image, "--control", "image", "--tag", "crecs-company-logo")
        code, out, err = run("unbind", "--element", image, "--control", "image", "--workdir", self.wd)
        self.assertEqual(0, code, out + err)
        self.assertNotIn("__dynamic__", self.element(image)["settings"])

    # -- reading it back ---------------------------------------------------------------------------

    def test_bind_list_shows_the_logo_tag_by_name_and_what_it_gives(self):
        image = self.add_image()["element_id"]
        self.bind(image, "--control", "image", "--tag", "crecs-flyer-logo")
        code, out, err = run("bind", "--list", "--element", image, "--workdir", self.wd)
        self.assertEqual(0, code, out + err)
        self.assertIn("crecs-flyer-logo", out)
        self.assertIn("Flyer logo", out)
        self.assertIn("picture", out)
        self.assertNotIn("None", out)
        code, out, _err = run("bind", "--list", "--element", image, "--workdir", self.wd, "--json")
        row = json.loads(out)["bindings"][0]
        self.assertEqual("crecs-flyer-logo", row["tag"])
        self.assertIsNone(row["param"])
        self.assertEqual("CRE Cloud: Flyer logo", row["tag_title"])
        self.assertEqual("a picture", row["gives"])
        self.assertIsNone(row.get("problem"))

    def test_bind_list_says_when_a_logo_tag_was_saved_without_its_settings_string(self):
        image = self.add_image()["element_id"]
        self.bind(image, "--control", "image", "--tag", "crecs-company-logo")
        path = os.path.join(self.wd, "document.json")
        doc = self.document()
        node = next(n for n in self.walk(doc["content"] if isinstance(doc, dict) else doc)
                    if n.get("id") == image)
        node["settings"]["__dynamic__"]["image"] = '[elementor-tag id="a1b2c3d" name="crecs-company-logo"]'
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        code, out, err = run("bind", "--list", "--element", image, "--workdir", self.wd,
                             "--accept-external")
        self.assertEqual(0, code, out + err)
        self.assertIn("settings", out)
        self.assertIn("prints nothing", out)
        code, out, _err = run("bind", "--list", "--element", image, "--workdir", self.wd,
                              "--accept-external", "--json")
        self.assertIn("settings", json.loads(out)["bindings"][0]["problem"])

    def test_the_catalog_lists_the_tags_a_binding_may_use(self):
        code, out, err = run("catalog", "--tags", "--json")
        self.assertEqual(0, code, out + err)
        names = {t["name"] for t in json.loads(out)["tags"]}
        self.assertEqual({"crecs-property", "crecs-company-logo", "crecs-flyer-logo"}, names,
                         "the forbidden tag and the popup tag are not for a binding to use")
        code, out, _err = run("catalog", "--tags")
        self.assertIn("crecs-company-logo", out)
        self.assertIn("a picture", out)


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
