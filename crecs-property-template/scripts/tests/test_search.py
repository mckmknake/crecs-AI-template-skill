"""The search page's layout document: the checks agree with the plugin, the commands edit
it the way they say, and a change the plugin would refuse is never written.

The conformance cases read tests/fixtures/search-vectors.json, which the plugin's
tools/search-layout/build-search-reference.php generates by running the plugin's own
checks on each sample. If this file and the plugin disagree on a single word, the skill
would tell a person something different from what the preview then does.
"""

import contextlib
import copy
import io
import json
import os
import shutil
import tempfile
import unittest

from crecs import search_cli
from crecs.search_layout import REFERENCE, Vocabulary, blocking, find, normalise
from crecs_preview import canonical_hash

HERE = os.path.dirname(os.path.abspath(__file__))
VECTORS = os.path.join(HERE, "fixtures", "search-vectors.json")

CODES = {"E-SL-SHAPE", "E-SL-ROOT", "E-SL-NODE", "E-SL-ID", "E-SL-BLOCK", "E-SL-ELTYPE",
         "E-SL-CHILDREN", "E-SL-REQUIRED", "E-SL-ONCE", "E-SL-WITHIN", "E-SL-NOT-WITHIN",
         "E-SL-SETTING", "E-SL-VALUE", "E-SL-LIMIT"}

# Ids in the built-in layout, as the reference records it.
PAGE, WRAPPER, MAP, FILTERS = "5e2a0001", "5e2a0002", "5e2a0004", "5e2a0005"
PROPERTY_TYPE, RATE, CLEAR = "5e2a0008", "5e2a000a", "5e2a000c"
LISTINGS, SORT = "5e2a000d", "5e2a000f"


def vectors():
    with open(VECTORS, encoding="utf-8") as fh:
        return json.load(fh)


class AgreesWithThePlugin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vocab = Vocabulary.load()
        cls.vectors = vectors()

    def test_every_value_gets_the_plugins_verdict(self):
        for sample in self.vectors["values"]:
            spec = self.vocab.controls(sample["block"])[sample["control"]]
            with self.subTest(control=sample["control"], value=sample["json"]):
                self.assertEqual(sample["problem"], self.vocab.problem(spec, json.loads(sample["json"])))

    def test_every_document_gets_the_plugins_findings(self):
        for sample in self.vectors["documents"]:
            with self.subTest(document=sample["name"]):
                self.assertEqual(sample["findings"], self.vocab.check(sample["document"]))

    def test_a_different_verdict_would_be_seen(self):
        # The cases above compare whole strings and whole finding lists; prove a single
        # changed word is enough to fail them.
        sample = copy.deepcopy(self.vectors["documents"][1])
        self.assertTrue(sample["findings"], "the second vector should have findings")
        sample["findings"][0]["message"] += " (changed)"
        self.assertNotEqual(sample["findings"], self.vocab.check(sample["document"]))

    def test_the_vectors_cover_every_value_type_and_every_code(self):
        types = {spec["type"] for block in self.vocab.blocks.values()
                 for spec in block["controls"].values()}
        sampled = {self.vocab.controls(s["block"])[s["control"]]["type"]
                   for s in self.vectors["values"]}
        self.assertEqual(set(), types - sampled, "value types with no vector")
        codes = {f["code"] for d in self.vectors["documents"] for f in d["findings"]}
        self.assertEqual(set(), CODES - codes, "finding codes with no vector")

    def test_the_built_in_layout_is_valid(self):
        self.assertEqual([], self.vocab.check(self.vocab.builtin))


class Commands(unittest.TestCase):

    def setUp(self):
        self.vocab = Vocabulary.load()
        self.dir = tempfile.mkdtemp(prefix="crecs-search-test-")
        self.path = os.path.join(self.dir, "search.json")
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.vocab.builtin, fh)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = search_cli.main(["--file", self.path] + list(args))
        return code, out.getvalue(), err.getvalue()

    def doc(self):
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def settings(self, node_id):
        node = find(self.doc(), node_id)[0]
        return node["settings"] if isinstance(node["settings"], dict) else {}

    def raw(self):
        with open(self.path, "rb") as fh:
            return fh.read()

    # -- set / unset -------------------------------------------------------------

    def test_a_colour_and_its_hover(self):
        self.assertEqual(0, self.run_cli("set", "--node", PROPERTY_TYPE, "--key",
                                         "button_background_color", "--value", "#0a3d62")[0])
        self.assertEqual(0, self.run_cli("set", "--node", PROPERTY_TYPE, "--key",
                                         "button_background_color", "--hover", "--value", "#145a8d")[0])
        self.assertEqual({"button_background_color": "#0a3d62",
                          "button_background_color_hover": "#145a8d"}, self.settings(PROPERTY_TYPE))
        self.assertEqual([], self.vocab.check(self.doc()))

    def test_a_bad_value_is_refused_and_nothing_is_written(self):
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", PROPERTY_TYPE, "--key",
                                       "button_background_color", "--value", "red")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("is not a colour", err)
        self.assertEqual(before, self.raw())

    def test_an_unknown_setting_is_refused_with_a_suggestion(self):
        code, _out, err = self.run_cli("set", "--node", PROPERTY_TYPE, "--key",
                                       "button_backgroundcolor", "--value", "#000")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("button_background_color", err)
        code, _out, err = self.run_cli("set", "--node", MAP, "--key", "map_zoom", "--value", "12")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("no map_zoom setting", err)

    def test_device_values_only_where_the_setting_is_responsive(self):
        self.assertEqual(0, self.run_cli("set", "--node", MAP, "--key", "map_height",
                                         "--device", "mobile", "--value", "240px")[0])
        self.assertEqual({"unit": "px", "size": 240}, self.settings(MAP)["map_height_mobile"])
        code, _out, err = self.run_cli("set", "--node", PROPERTY_TYPE, "--key",
                                       "button_font_weight", "--device", "mobile", "--value", "700")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("every device", err)

    def test_shorthand_values(self):
        self.run_cli("set", "--node", FILTERS, "--key", "_width", "--value", "300px")
        self.run_cli("set", "--node", FILTERS, "--key", "panel_padding", "--value", "8px 16px")
        self.run_cli("set", "--node", FILTERS, "--key", "panel_box_shadow",
                     "--value", "0 2px 8px 0 rgba(0,0,0,0.2)")
        self.run_cli("set", "--node", FILTERS, "--key", "direction", "--value", "column")
        settings = self.settings(FILTERS)
        self.assertEqual({"unit": "px", "size": 300}, settings["_width"])
        self.assertEqual({"unit": "px", "top": 8, "right": 16, "bottom": 8, "left": 16,
                          "isLinked": False}, settings["panel_padding"])
        self.assertEqual({"horizontal": 0, "vertical": 2, "blur": 8, "spread": 0,
                          "color": "rgba(0,0,0,0.2)"}, settings["panel_box_shadow"])
        self.assertEqual([], self.vocab.check(self.doc()))

    def test_switch_no_removes_the_setting(self):
        self.run_cli("set", "--node", LISTINGS, "--key", "_grow", "--value", "yes")
        self.assertEqual("yes", self.settings(LISTINGS)["_grow"])
        self.run_cli("set", "--node", LISTINGS, "--key", "_grow", "--value", "no")
        self.assertNotIn("_grow", self.settings(LISTINGS))

    def test_unset_leaves_an_empty_list_as_the_plugin_stores_it(self):
        self.run_cli("set", "--node", MAP, "--key", "map_height", "--value", "300px")
        self.run_cli("unset", "--node", MAP, "--key", "map_height")
        node = find(self.doc(), MAP)[0]
        self.assertEqual([], node["settings"])
        # And so the skill's hash of the untouched layout is the one the site reports.
        self.assertEqual(canonical_hash(normalise(copy.deepcopy(self.vocab.builtin))["content"]),
                         canonical_hash(self.doc()["content"]))

    # -- texts -------------------------------------------------------------------

    def test_a_text_is_set_and_put_back(self):
        self.assertEqual(0, self.run_cli("text", "--node", PROPERTY_TYPE, "--slot", "button",
                                         "--value", "Tipo de imóvel")[0])
        self.assertEqual("Tipo de imóvel", self.settings(PROPERTY_TYPE)["text_button"])
        self.run_cli("text", "--node", PROPERTY_TYPE, "--slot", "button", "--reset")
        self.assertNotIn("text_button", self.settings(PROPERTY_TYPE))
        code, _out, err = self.run_cli("text", "--node", PROPERTY_TYPE, "--slot", "title",
                                       "--value", "x")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("its texts: button", err)

    def test_a_text_on_two_lines_is_refused(self):
        code, _out, err = self.run_cli("text", "--node", CLEAR, "--slot", "label",
                                       "--value", "Clear\nall")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("one line", err)

    # -- structure ---------------------------------------------------------------

    def test_the_sort_cannot_go_into_the_filters(self):
        before = self.raw()
        code, _out, err = self.run_cli("move", "--node", SORT, "--into", FILTERS)
        self.assertEqual(search_cli.EXIT_REFUSED, code)
        self.assertIn("E-SL-NOT-WITHIN", err)
        self.assertEqual(before, self.raw())

    def test_a_filter_cannot_leave_the_filters(self):
        code, _out, err = self.run_cli("move", "--node", RATE, "--before", SORT)
        self.assertEqual(search_cli.EXIT_REFUSED, code)
        self.assertIn("E-SL-WITHIN", err)

    def test_moving_within_the_filters(self):
        self.assertEqual(0, self.run_cli("move", "--node", CLEAR, "--into", FILTERS,
                                         "--position", "0")[0])
        filters = find(self.doc(), FILTERS)[0]
        self.assertEqual(CLEAR, filters["elements"][0]["id"])

    def test_a_block_cannot_go_inside_itself(self):
        code, _out, err = self.run_cli("move", "--node", WRAPPER, "--into", FILTERS)
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("inside itself", err)

    def test_filters_beside_the_results_in_a_box_and_back(self):
        code, out, _err = self.run_cli("--json", "add-box", "--wrap", FILTERS + "," + LISTINGS,
                                       "--direction", "row")
        self.assertEqual(0, code)
        result = json.loads(out)
        self.assertEqual([FILTERS, LISTINGS], result["holds"])
        self.assertIn("direction", result.get("hint", ""), "the main area's layout was not mentioned")
        box = find(self.doc(), result["node"])[0]
        self.assertEqual("crecs_search_box", box["widgetType"])
        self.assertEqual([], self.vocab.check(self.doc()))

        self.assertEqual(0, self.run_cli("remove-box", "--node", result["node"])[0])
        self.assertEqual(self.vocab.builtin["content"], self.doc()["content"])

    def test_only_a_box_can_be_removed(self):
        code, _out, err = self.run_cli("remove-box", "--node", MAP)
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("not a box", err)

    def test_a_box_cannot_hold_what_it_sits_in(self):
        code, _out, err = self.run_cli("add-box", "--into", FILTERS, "--wrap", FILTERS)
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("sits in", err)

    def test_hiding_only_where_the_page_allows_it(self):
        code, out, _err = self.run_cli("--json", "add-box", "--into", WRAPPER)
        box = json.loads(out)["node"]
        self.assertEqual(0, self.run_cli("hide", "--node", box, "--device", "mobile")[0])
        self.assertEqual("yes", self.settings(box)["_hide_mobile"])
        code, _out, err = self.run_cli("hide", "--node", MAP, "--device", "mobile")
        self.assertEqual(search_cli.EXIT_USAGE, code)
        self.assertIn("_hide_mobile", err)

    # -- the file ----------------------------------------------------------------

    def test_the_file_can_be_named_before_or_after_the_command(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = search_cli.main(["show", "--file", self.path])
        self.assertEqual(0, code)
        self.assertIn("Property type filter", out.getvalue())

    def test_a_property_template_is_refused(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"version": "0.4", "type": "page", "content": []}, fh)
        code, _out, err = self.run_cli("show")
        self.assertEqual(search_cli.EXIT_FILE, code)
        self.assertIn("crecs_template.py", err)

    def test_an_export_payload_is_read_as_its_document(self):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump({"document": self.vocab.builtin, "manifest": {"kind": "search"}}, fh)
        self.assertEqual(0, self.run_cli("validate")[0])

    def test_validate_reports_what_the_plugin_would_refuse(self):
        doc = copy.deepcopy(self.vocab.builtin)
        wrapper = find(doc, WRAPPER)[0]
        wrapper["elements"] = [n for n in wrapper["elements"] if n["id"] != MAP]
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        code, out, _err = self.run_cli("validate")
        self.assertEqual(search_cli.EXIT_REFUSED, code)
        self.assertIn("E-SL-REQUIRED", out)
        self.assertTrue(blocking(self.vocab.check(doc)))


class Reference(unittest.TestCase):

    def test_the_reference_is_the_plugins(self):
        with open(REFERENCE, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn("Generated by the CRE Cloud Solutions plugin", data["_comment"])
        self.assertEqual({"type": "crecs-search-layout", "version": 1}, data["document"])

    def test_every_block_in_the_built_in_layout_is_known(self):
        vocab = Vocabulary.load()
        for node, *_ in search_cli.walk(vocab.builtin):
            self.assertIn(node["widgetType"], vocab.blocks)


if __name__ == "__main__":
    unittest.main()
