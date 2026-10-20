"""The property flyer's layout document: the checks agree with the plugin, the commands edit
it the way they say, and a change the plugin would refuse is never written.

The conformance cases read tests/fixtures/flyer-vectors.json, which the plugin's
tools/flyer-layout/build-flyer-reference.php generates by running the plugin's own checks
(Crecs_Flyer_Layout_Controls::problem(), Crecs_Flyer_Layout_Validate::check() and
Crecs_Flyer_Layout::option()) on each sample. If this file and the plugin disagree on a
single word, the skill would tell a person something different from what the preview then
does.

The command cases work on a temporary copy of the vectors' design that uses every block;
nothing here touches the network.
"""

import contextlib
import copy
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from unittest import mock

from crecs import flyer_cli, flyer_layout
from crecs.flyer_layout import REFERENCE, Vocabulary, blocking, find, normalise

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
VECTORS = os.path.join(HERE, "fixtures", "flyer-vectors.json")
MARKDOWN = os.path.join(os.path.dirname(REFERENCE), "FLYER-LAYOUT.md")

CODES = {"E-FL-SHAPE", "E-FL-ROOT", "E-FL-REQUIRED", "E-FL-ONCE", "E-FL-PAGES", "E-FL-LIMIT",
         "E-FL-NODE", "E-FL-ID", "E-FL-BLOCK", "E-FL-ELTYPE", "E-FL-CHILDREN", "E-FL-WITHIN",
         "E-FL-SETTING", "E-FL-VALUE", "E-FL-FONT"}

# The vectors' design that uses every block, and its ids.
SAMPLE = "a design using every block"
ROOT, HEADER, FOOTER, PAGE1, PAGE2 = "flyer001", "header01", "footer01", "page0001", "page0002"
HROW, HCOL1, HCOL2, NAME, ADDRESS, LOGO = "hrow0001", "hcol0001", "hcol0002", "name0001", "addr0001", "logo0001"
FROW, COMPANY, DISCLAIMER = "frow0001", "comp0001", "disc0001"
PROW1, PCOL1, PCOL2 = "prow0001", "pcol0001", "pcol0002"
BADGE, HEADLINE, PHOTO, GRID, DESCRIPTION = "badge001", "head0001", "photo001", "grid0001", "desc0001"
FACTS, HIGHLIGHTS, NROW, NCOL1, NCOL2, MAP, SPACER, DIVIDER = (
    "facts001", "high0001", "nrow0001", "ncol0001", "ncol0002", "map00001", "spac0001", "divi0001")
PROW2, PCOL3, SUITES, CONTACTS, TEXT = "prow0002", "pcol0003", "suit0001", "cont0001", "text0001"


def vectors():
    with open(VECTORS, encoding="utf-8") as fh:
        return json.load(fh)


def sample_document():
    for sample in vectors()["documents"]:
        if sample["name"] == SAMPLE:
            return copy.deepcopy(sample["document"])
    raise AssertionError("the vectors have no %r document" % SAMPLE)


LOGO_BLOCK = "crecs_flyer_logo"
# The plugin's message for more Logo blocks than it allows (Crecs_Flyer_Layout_Validate::check()).
LOGO_LIMIT = ("The flyer has %d Logo blocks (crecs_flyer_logo); it may have at most 2, because each one "
              "carries a whole image that every page of its band prints again, and so does each "
              "attachment frame.")


def with_logos(count):
    """The design using every block, whose one Logo block is made `count` of them."""
    doc = sample_document()
    column = find(doc, PCOL3)[0]
    for i in range(count - 1):
        column["elements"].append({"id": "xlogo%03d" % i, "elType": "widget", "widgetType": LOGO_BLOCK,
                                   "settings": {}, "elements": []})
    return doc


def vector_document(sample):
    """A document vector: PHP's own array, or JSON text PHP decoded (to keep {} and {"0": …})."""
    return json.loads(sample["json"]) if "json" in sample else copy.deepcopy(sample["document"])


class AgreesWithThePlugin(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.vocab = Vocabulary.load()
        cls.vectors = vectors()

    def test_every_value_gets_the_plugins_verdict(self):
        self.assertTrue(self.vectors["values"])
        for sample in self.vectors["values"]:
            spec = self.vocab.controls(sample["block"])[sample["control"]]
            with self.subTest(block=sample["block"], control=sample["control"], value=sample["json"]):
                self.assertEqual(sample["problem"], self.vocab.problem(spec, json.loads(sample["json"])))

    def test_every_document_gets_the_plugins_findings(self):
        self.assertTrue(self.vectors["documents"])
        for sample in self.vectors["documents"]:
            with self.subTest(document=sample["name"]):
                self.assertEqual(sample["findings"], self.vocab.check(vector_document(sample)))

    def test_every_option_reads_as_the_plugin_reads_it(self):
        self.assertTrue(self.vectors["options"])
        for sample in self.vectors["options"]:
            with self.subTest(option=sample["name"], node=json.dumps(sample["node"])[:80]):
                self.assertEqual(sample["value"], self.vocab.option(sample["node"], sample["name"]))

    def test_a_different_verdict_would_be_seen(self):
        # The cases above compare whole strings and whole finding lists; prove a single
        # changed word is enough to fail them.
        sample = next(copy.deepcopy(s) for s in self.vectors["documents"] if s["findings"])
        sample["findings"][0]["message"] += " (changed)"
        self.assertNotEqual(sample["findings"], self.vocab.check(vector_document(sample)))
        value = next(copy.deepcopy(s) for s in self.vectors["values"] if s["problem"])
        spec = self.vocab.controls(value["block"])[value["control"]]
        self.assertNotEqual(value["problem"] + " (changed)", self.vocab.problem(spec, json.loads(value["json"])))

    def test_the_vectors_cover_every_value_type_and_every_code(self):
        types = {spec["type"] for block in self.vocab.blocks.values()
                 for spec in block["controls"].values()}
        sampled = {self.vocab.controls(s["block"])[s["control"]]["type"] for s in self.vectors["values"]}
        self.assertEqual(set(), types - sampled, "value types with no vector")
        codes = {f["code"] for d in self.vectors["documents"] for f in d["findings"]}
        self.assertEqual(set(), CODES - codes, "finding codes with no vector")
        self.assertEqual(CODES, set(self.vocab.codes), "the reference's codes are not the validator's")

    def test_the_vectors_hold_an_example_of_every_rule(self):
        # A rule with no vector would let the port drift from the plugin unseen.
        messages = [(f["code"], f["message"]) for d in self.vectors["documents"] for f in d["findings"]]
        rules = {
            "a document's own keys": ("E-FL-SHAPE", r"^The document has \"[^\"]+\", a key no flyer"),
            "a document's own keys, several": ("E-FL-SHAPE", r"^The document has \"[^\"]+\", \"[^\"]+\", keys no flyer"),
            "a block's own keys": ("E-FL-NODE", r"^The block has \"[^\"]+\", a key no block has"),
            "a block's own keys, several": ("E-FL-NODE", r"^The block has \"[^\"]+\", \"[^\"]+\", keys no block has"),
            "a fixed height": ("E-FL-VALUE", r"^crecs_flyer_[a-z_]+ \"[a-z_]+\" leaves less than 10 px for what the block holds"),
            "a band's height": ("E-FL-VALUE", r"^crecs_flyer_(header|footer) \"height\" leaves less than"),
            "a row's height": ("E-FL-VALUE", r"^crecs_flyer_row \"height\" leaves less than"),
            "a page's room": ("E-FL-VALUE", r"^The flyer's padding and border, the header and footer heights .* 816 px a landscape page"),
            "a row's columns and gaps": ("E-FL-VALUE", r"^The [0-9]+ columns of this row, at least 40 px each"),
            "a row's widths": ("E-FL-VALUE", r"^The columns of this row"),
            "a map's boundaries": ("E-FL-VALUE", r"^crecs_flyer_map \"boundaries\" is \"on\", which only a satellite or hybrid map can show; this map is a road map"),
            "the logo limit": ("E-FL-LIMIT", r"^The flyer has [0-9]+ Logo blocks \(crecs_flyer_logo\); it may have at most 2, because each one carries a whole image"),
            "the block and depth limit": ("E-FL-LIMIT", r"^The document has [0-9]+ blocks nested [0-9]+ deep; a flyer may have at most 150 blocks, 8 deep\.$"),
        }
        for rule, (code, pattern) in rules.items():
            with self.subTest(rule=rule):
                self.assertTrue(any(c == code and re.search(pattern, m) for c, m in messages), rule)
        problems = [s["problem"] or "" for s in self.vectors["values"]]
        for rule, pattern in {"hex alpha": r"write it as rgba\(10, 61, 98, 0\.502\)",
                              "a size's own keys": r"^may hold only \"unit\", \"size\", not \"sizes\"$",
                              "four sides' own keys": r"^may hold only \"unit\", \"top\", .*\"isLinked\", not \"important\"$"}.items():
            with self.subTest(rule=rule):
                self.assertTrue(any(re.search(pattern, p) for p in problems), rule)
        refused = {s["json"] for s in self.vectors["values"] if s["problem"]}
        for json_text in ('{"unit":"px","size":13.1234}', '{"unit":"px","size":1e400}', '[1,2,3,4]'):
            self.assertIn(json_text, refused)
        accepted = {s["json"] for s in self.vectors["values"] if s["problem"] is None}
        for json_text in ('{"unit":"px","size":1e1}', '{"unit":"px","size":13.125}', '[]'):
            self.assertIn(json_text, accepted)
        normalised = [s for s in self.vectors["options"] if isinstance(s["node"], dict)
                      and s["node"].get("id") == "opt00020" and s["name"] == "name_padding"]
        self.assertEqual([{"unit": "px", "top": 4, "right": 8.5, "bottom": 0.25, "left": 8}],
                         [s["value"] for s in normalised])

    def test_option_never_gives_a_number_as_text(self):
        node = {"id": "opt0nrm1", "elType": "widget", "widgetType": "crecs_flyer_name", "settings": {
            "name_font_size": {"unit": "px", "size": "14"},
            "name_padding": {"unit": "px", "top": "4", "right": "8.5", "bottom": 0, "left": 2, "isLinked": False}}}
        size = self.vocab.option(node, "name_font_size")
        self.assertEqual({"unit": "px", "size": 14}, size)
        self.assertIsInstance(size["size"], int)
        padding = self.vocab.option(node, "name_padding")
        self.assertEqual({"unit": "px", "top": 4, "right": 8.5, "bottom": 0, "left": 2}, padding)
        self.assertIsInstance(padding["right"], float)

    def test_extent_reads_padding_and_border(self):
        settings = {"band_padding": {"unit": "px", "top": "4", "right": 10, "bottom": 6.5, "left": 12},
                    "band_border_width": {"unit": "px", "top": 3, "right": 1, "bottom": 0, "left": 1},
                    "row_padding": {"unit": "px", "top": 101, "right": 0, "bottom": 0, "left": 0}}
        self.assertEqual({"h": 24.0, "v": 13.5}, self.vocab.extent(settings, "band"))
        self.assertEqual({"h": 0.0, "v": 0.0}, self.vocab.extent(settings, "row"))
        self.assertEqual({"h": 0.0, "v": 0.0}, self.vocab.extent([], "band"))
        self.assertEqual({"h": 0.0, "v": 0.0}, self.vocab.extent(None, "band"))

    def test_a_bands_padding_and_border_are_inside_its_height(self):
        # A page's room counts a band's height alone: a design whose bands are padded nearly
        # full is accepted, though adding their padding and border again (the rule before)
        # would have refused it.
        sample = next(s for s in self.vectors["documents"]
                      if s["name"] == "tall bands whose padding and border sit inside their heights")
        doc = vector_document(sample)
        self.assertEqual([], sample["findings"])
        self.assertEqual([], self.vocab.check(doc))
        root = doc["content"][0]
        bands = [n for n in root["elements"] if n["widgetType"] in ("crecs_flyer_header", "crecs_flyer_footer")]
        page = next(n for n in root["elements"] if n["widgetType"] == "crecs_flyer_page")
        heights = sum(self.vocab.option(band, "height") for band in bands)
        inside = sum(self.vocab.extent(band["settings"], "band")["v"] for band in bands)
        others = self.vocab.extent(root["settings"], "page")["v"] + self.vocab.extent(page["settings"], "body")["v"]
        short, least = self.vocab.smallest_page(1)[1], self.vocab.limits["min_body"]
        self.assertGreater(inside, 0)
        self.assertGreaterEqual(short - (heights + others), least, "the rule now accepts it")
        self.assertLess(short - (heights + inside + others), least, "the rule before refused it")

    def test_a_maps_boundaries_need_an_aerial_map(self):
        # The plugin's rule (Crecs_Flyer_Layout_Validate::check_together()): the property's
        # boundaries are drawn only on a satellite or hybrid map. A road map, chosen or by
        # default, with boundaries "on" is refused with the plugin's own words.
        refused = ('crecs_flyer_map "boundaries" is "on", which only a satellite or hybrid map can '
                   'show; this map is a road map (its "map_type"), so set "map_type" to "satellite" '
                   'or "hybrid", or "boundaries" to "off".')

        def findings(settings):
            doc = sample_document()
            find(doc, MAP)[0]["settings"] = settings
            return self.vocab.check(doc)

        for settings in ({}, {"map_type": "road"}, {"boundaries": "off"},
                         {"map_type": "road", "boundaries": "off"}, {"map_type": "satellite"},
                         {"map_type": "hybrid"}, {"map_type": "hybrid", "zoom": 17, "height": 300},
                         {"map_type": "satellite", "boundaries": "on"},
                         {"map_type": "hybrid", "boundaries": "on", "zoom": 21}):
            with self.subTest(accepted=settings):
                self.assertEqual([], findings(settings))
        for settings in ({"boundaries": "on"}, {"map_type": "road", "boundaries": "on"},
                         {"map_type": "", "boundaries": "on"}):
            with self.subTest(refused=settings):
                found = findings(settings)
                self.assertEqual([{"level": "error", "code": "E-FL-VALUE", "node": MAP,
                                   "message": refused}], found)
                self.assertTrue(blocking(found))
        # A zoom outside 1 to 21 is refused by the control, on its own.
        for zoom in (0, 22, 16.5):
            with self.subTest(zoom=zoom):
                found = findings({"map_type": "satellite", "zoom": zoom})
                self.assertEqual(["E-FL-VALUE"], [f["code"] for f in found])
                self.assertIn('"zoom"', found[0]["message"])

    def test_the_logo_limit_is_the_plugins(self):
        # `max` on the Logo block and limits.max_logos: the plugin's MAX_LOGOS, read from the
        # reference like every other limit.
        self.assertEqual(2, self.vocab.limits["max_logos"])
        self.assertEqual(2, self.vocab.blocks[LOGO_BLOCK]["max"])
        others = {t: b.get("max") for t, b in self.vocab.blocks.items() if t != LOGO_BLOCK}
        self.assertEqual({}, {t: m for t, m in others.items() if m is not None},
                         "only the Logo block has a count limit today")

    def test_a_third_logo_gets_the_plugins_finding_word_for_word(self):
        for count in (1, 2):
            with self.subTest(logos=count):
                self.assertEqual([], self.vocab.check(with_logos(count)))
        for count in (3, 5):
            with self.subTest(logos=count):
                findings = self.vocab.check(with_logos(count))
                self.assertEqual([{"level": "error", "code": "E-FL-LIMIT", "node": None,
                                   "message": LOGO_LIMIT % count}], findings)
                self.assertTrue(blocking(findings))

    def test_the_logo_limit_is_told_beside_the_block_and_depth_limit(self):
        # Both are E-FL-LIMIT with no node: a design over both gets both, the logo one first
        # (the plugin checks the block types before it counts blocks and depth).
        doc = with_logos(3)
        column = find(doc, PCOL3)[0]
        for i in range(self.vocab.limits["max_nodes"]):
            column["elements"].append({"id": "xspc%04d" % i, "elType": "widget",
                                       "widgetType": "crecs_flyer_spacer", "settings": {}, "elements": []})
        findings = [f for f in self.vocab.check(doc) if f["code"] == "E-FL-LIMIT"]
        self.assertEqual(2, len(findings))
        self.assertEqual(LOGO_LIMIT % 3, findings[0]["message"])
        self.assertRegex(findings[1]["message"], r"^The document has [0-9]+ blocks nested [0-9]+ deep; a flyer may have at most 150 blocks, 8 deep\.$")

    def test_the_design_using_every_block_is_valid_and_uses_every_block(self):
        doc = sample_document()
        self.assertEqual([], self.vocab.check(doc))
        used = {node["widgetType"] for node, *_ in flyer_layout.walk(doc)}
        self.assertEqual(set(self.vocab.blocks), used)

    def test_every_built_in_design_is_valid(self):
        for name, document in self.vocab.builtins.items():
            with self.subTest(design=name):
                self.assertEqual([], self.vocab.check(document))


class Commands(unittest.TestCase):

    def setUp(self):
        self.vocab = Vocabulary.load()
        self.dir = tempfile.mkdtemp(prefix="crecs-flyer-test-")
        self.path = os.path.join(self.dir, "flyer.json")
        self.write(sample_document())

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, document, path=None):
        with open(path or self.path, "w", encoding="utf-8") as fh:
            json.dump(document, fh)

    def run_cli(self, *args, path=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = flyer_cli.main(["--file", path or self.path] + list(args))
        return code, out.getvalue(), err.getvalue()

    def doc(self):
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def node(self, node_id):
        return find(self.doc(), node_id)[0]

    def settings(self, node_id):
        node = self.node(node_id)
        return node["settings"] if isinstance(node["settings"], dict) else {}

    def children(self, node_id):
        return [child["id"] for child in self.node(node_id)["elements"]]

    def raw(self):
        with open(self.path, "rb") as fh:
            return fh.read()

    def assertValid(self):
        self.assertEqual([], self.vocab.check(self.doc()))

    # -- set / unset -------------------------------------------------------------

    def test_a_colour_a_size_and_a_font(self):
        for key, value in (("name_color", "#0a3d62"), ("name_font_size", "32px"),
                           ("name_font_family", "URW Gothic L")):
            self.assertEqual(0, self.run_cli("set", "--node", NAME, "--key", key, "--value", value)[0], key)
        settings = self.settings(NAME)
        self.assertEqual("#0a3d62", settings["name_color"])
        self.assertEqual({"unit": "px", "size": 32}, settings["name_font_size"])
        self.assertEqual("URW Gothic L", settings["name_font_family"])
        self.assertValid()

    def test_a_bad_value_is_refused_and_nothing_is_written(self):
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", NAME, "--key", "name_color", "--value", "red")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("is not a colour", err)
        self.assertEqual(before, self.raw())

    def test_a_font_the_printer_lacks_is_refused(self):
        code, _out, err = self.run_cli("set", "--node", NAME, "--key", "name_font_family", "--value", "Arial")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("fonts the flyer printer has", err)
        self.assertIn("Lato", err)

    def test_an_unknown_setting_is_refused_with_a_suggestion(self):
        code, _out, err = self.run_cli("set", "--node", NAME, "--key", "name_colour", "--value", "#000")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("name_color", err)
        for key in ("name_color_hover", "name_font_size_mobile"):
            code, _out, err = self.run_cli("set", "--node", NAME, "--key", key, "--value", "#000")
            self.assertEqual(flyer_cli.EXIT_USAGE, code, key)
            self.assertIn("printed", err, key)

    def test_shorthand_values(self):
        for node, key, value in ((NAME, "name_padding", "4px 8px"),
                                 (DESCRIPTION, "description_line_height", "1.4"),
                                 (DIVIDER, "rule_width", "50%"),
                                 (PHOTO, "height", "280px"),
                                 (NROW, "height", "auto"),
                                 (FACTS, "fields", "total_sf, rates")):
            self.assertEqual(0, self.run_cli("set", "--node", node, "--key", key, "--value", value)[0], key)
        self.assertEqual({"unit": "px", "top": 4, "right": 8, "bottom": 4, "left": 8, "isLinked": False},
                         self.settings(NAME)["name_padding"])
        self.assertEqual({"unit": "", "size": 1.4}, self.settings(DESCRIPTION)["description_line_height"])
        self.assertEqual({"unit": "%", "size": 50}, self.settings(DIVIDER)["rule_width"])
        self.assertEqual(280, self.settings(PHOTO)["height"])
        self.assertEqual("auto", self.settings(NROW)["height"])
        self.assertEqual(["total_sf", "rates"], self.settings(FACTS)["fields"])
        self.assertValid()

    def test_numbers_are_whole(self):
        for value in ("2.5", "tall"):
            code, _out, err = self.run_cli("set", "--node", PHOTO, "--key", "index", "--value", value)
            self.assertEqual(flyer_cli.EXIT_USAGE, code, value)
        code, _out, err = self.run_cli("set", "--node", PHOTO, "--key", "index", "--value", "31")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("from 1 to 30", err)

    def test_unset_leaves_an_empty_list_as_the_plugin_stores_it(self):
        self.assertEqual(0, self.run_cli("set", "--node", HEADLINE, "--key", "headline_color",
                                         "--value", "#333333")[0])
        self.assertEqual(0, self.run_cli("unset", "--node", HEADLINE, "--key", "headline_color")[0])
        self.assertEqual([], self.node(HEADLINE)["settings"])

    # -- texts -------------------------------------------------------------------

    def test_a_text_is_set_and_put_back(self):
        self.assertEqual(0, self.run_cli("text", "--node", FACTS, "--slot", "total_sf",
                                         "--value", "Área total")[0])
        self.assertEqual("Área total", self.settings(FACTS)["text_total_sf"])
        self.assertEqual(0, self.run_cli("text", "--node", FACTS, "--slot", "total_sf", "--reset")[0])
        self.assertNotIn("text_total_sf", self.settings(FACTS))
        code, _out, err = self.run_cli("text", "--node", FACTS, "--slot", "price", "--value", "x")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("its texts: total_sf", err)

    def test_line_breaks_only_where_the_text_takes_them(self):
        self.assertEqual(0, self.run_cli("text", "--node", TEXT, "--slot", "text",
                                         "--value", "Call today.\\nTours by appointment.")[0])
        self.assertEqual("Call today.\nTours by appointment.", self.settings(TEXT)["text_text"])
        before = self.raw()
        code, _out, err = self.run_cli("text", "--node", FACTS, "--slot", "rates", "--value", "Rate\\nper year")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("one line", err)
        self.assertEqual(before, self.raw())

    # -- the page ----------------------------------------------------------------

    def test_the_orientation(self):
        code, out, _err = self.run_cli("orientation", "portrait")
        self.assertEqual(0, code)
        self.assertEqual("portrait", self.settings(ROOT)["orientation"])
        self.assertIn("816 x 1056", out)
        code, _out, err = self.run_cli("orientation", "square")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn('"landscape", "portrait"', err)
        self.assertValid()

    # -- structure ---------------------------------------------------------------

    def test_adding_blocks_where_they_go(self):
        code, out, _err = self.run_cli("--json", "add", "--type", "photo", "--into", PCOL3)
        self.assertEqual(0, code)
        added = json.loads(out)["node"]
        self.assertEqual(added, self.children(PCOL3)[-1])
        node = self.node(added)
        self.assertEqual(("widget", "crecs_flyer_photo"), (node["elType"], node["widgetType"]))
        self.assertTrue(self.vocab.is_id(added))
        self.assertValid()

        before = self.raw()
        code, _out, err = self.run_cli("add", "--type", "photo", "--into", PAGE2)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-WITHIN", err)
        self.assertEqual(before, self.raw())

    def test_a_row_with_its_columns_and_a_page_in_the_flyer(self):
        code, out, _err = self.run_cli("--json", "add", "--type", "row", "--into", PAGE2, "--columns", "2")
        self.assertEqual(0, code)
        row = self.node(json.loads(out)["node"])
        self.assertEqual(["crecs_flyer_column"] * 2, [c["widgetType"] for c in row["elements"]])

        code, out, _err = self.run_cli("--json", "add", "--type", "page")
        self.assertEqual(0, code)
        self.assertEqual(json.loads(out)["node"], self.children(ROOT)[-1])
        self.assertEqual(0, self.run_cli("add", "--type", "page")[0])
        before = self.raw()
        code, _out, err = self.run_cli("add", "--type", "page")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-PAGES", err)
        self.assertEqual(before, self.raw())
        self.assertValid()

    def test_what_add_will_not_guess(self):
        code, _out, err = self.run_cli("add", "--type", "video", "--into", PCOL3)
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("no video block", err)
        code, _out, err = self.run_cli("add", "--type", "crecs_flyer", "--into", PCOL3)
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        code, _out, err = self.run_cli("add", "--type", "photo")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("say where", err)
        self.assertEqual(0, self.run_cli("add", "--type", "photo", "--into", PCOL3, "--id", "photo002")[0])
        code, _out, err = self.run_cli("add", "--type", "photo", "--into", PCOL3, "--id", "photo002")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("photo002", err)

    def logos(self):
        return [n["id"] for n, *_ in flyer_layout.walk(self.doc()) if n["widgetType"] == LOGO_BLOCK]

    def test_a_third_logo_is_refused_plainly_and_nothing_is_written(self):
        code, out, _err = self.run_cli("--json", "add", "--type", "logo", "--into", PCOL3)
        self.assertEqual(0, code)
        self.assertEqual(2, len(self.logos()))
        self.assertValid()
        before = self.raw()
        code, out, err = self.run_cli("add", "--type", "logo", "--into", PCOL3)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertEqual("", out)
        self.assertIn("refused", err)
        self.assertIn("nothing was written", err)
        self.assertIn("E-FL-LIMIT", err)
        self.assertIn(LOGO_LIMIT % 3, err)
        self.assertEqual(before, self.raw())
        self.assertEqual(2, len(self.logos()))

    def test_boundaries_on_a_street_map_are_refused_so_the_kind_of_map_is_set_first(self):
        # What SKILL.md tells the assistant: the satellite or hybrid map first, then the
        # boundaries. The other order leaves the design refused, and nothing is written.
        before = self.raw()
        code, out, err = self.run_cli("set", "--node", MAP, "--key", "boundaries", "--value", "on")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertEqual("", out)
        self.assertIn("nothing was written", err)
        self.assertIn("E-FL-VALUE", err)
        self.assertIn("only a satellite or hybrid map can show", err)
        self.assertEqual(before, self.raw())
        for key, value in (("map_type", "hybrid"), ("boundaries", "on"), ("zoom", "17")):
            self.assertEqual(0, self.run_cli("set", "--node", MAP, "--key", key, "--value", value)[0], key)
        settings = self.settings(MAP)
        self.assertEqual(("hybrid", "on", 17), (settings["map_type"], settings["boundaries"], settings["zoom"]))
        self.assertValid()
        # Going back to a street map while the boundaries are on is refused the same way.
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", MAP, "--key", "map_type", "--value", "road")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("only a satellite or hybrid map can show", err)
        self.assertEqual(before, self.raw())
        # Taking the boundaries off first lets the street map back.
        self.assertEqual(0, self.run_cli("set", "--node", MAP, "--key", "boundaries", "--value", "off")[0])
        self.assertEqual(0, self.run_cli("set", "--node", MAP, "--key", "map_type", "--value", "road")[0])
        self.assertValid()

    def test_a_zoom_the_map_cannot_have_is_refused_and_nothing_is_written(self):
        before = self.raw()
        for value in ("0", "22", "16.5", "close"):
            code, _out, err = self.run_cli("set", "--node", MAP, "--key", "zoom", "--value", value)
            self.assertEqual(flyer_cli.EXIT_USAGE, code, value)
            self.assertIn("zoom", err)
            self.assertEqual(before, self.raw())
        self.assertEqual(0, self.run_cli("set", "--node", MAP, "--key", "zoom", "--value", "21")[0])
        self.assertEqual(21, self.settings(MAP)["zoom"])

    def test_a_logo_moved_or_changed_is_not_a_new_logo(self):
        # Two logos are allowed; moving one, or setting its height, adds no finding.
        self.assertEqual(0, self.run_cli("add", "--type", "logo", "--into", PCOL3, "--id", "logo0002")[0])
        self.assertEqual(0, self.run_cli("move", "--node", "logo0002", "--into", PCOL1)[0])
        self.assertEqual(0, self.run_cli("set", "--node", "logo0002", "--key", "height", "--value", "40")[0])
        self.assertValid()

    def test_a_design_over_the_logo_limit_is_mended_one_logo_at_a_time(self):
        # A design that already has four is refused by the plugin; taking one out still has
        # three, the same problem counting less, so it is written, with the warning that the
        # preview still refuses. The second removal leaves it valid.
        doc = with_logos(4)
        self.write(doc)
        self.assertEqual(flyer_cli.EXIT_REFUSED, self.run_cli("validate")[0])
        code, _out, err = self.run_cli("remove", "--node", "xlogo000")
        self.assertEqual(0, code)
        self.assertIn("written, but the plugin would still refuse the flyer", err)
        self.assertIn(LOGO_LIMIT % 3, err)
        code, _out, err = self.run_cli("remove", "--node", "xlogo001")
        self.assertEqual(0, code)
        self.assertEqual("", err)
        self.assertValid()
        # And a design at the limit cannot be taken back over it by the same step.
        self.write(with_logos(2))
        code, _out, err = self.run_cli("add", "--type", "logo", "--into", PCOL1)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn(LOGO_LIMIT % 3, err)

    def test_a_block_by_its_short_name_or_its_label(self):
        for name in ("crecs_flyer_photo_grid", "photo_grid", "photo-grid", "Photo grid"):
            code, out, _err = self.run_cli("--json", "add", "--type", name, "--into", PCOL3)
            self.assertEqual(0, code, name)
            self.assertEqual("crecs_flyer_photo_grid", self.node(json.loads(out)["node"])["widgetType"], name)

    def test_removing_blocks(self):
        code, out, _err = self.run_cli("--json", "remove", "--node", NROW)
        self.assertEqual(0, code)
        self.assertEqual(5, json.loads(out)["blocks_removed"])
        self.assertNotIn(NROW, self.children(PCOL2))
        self.assertValid()

        before = self.raw()
        code, _out, err = self.run_cli("remove", "--node", HEADER)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-REQUIRED", err)
        self.assertEqual(before, self.raw())
        code, _out, err = self.run_cli("remove", "--node", ROOT)
        self.assertEqual(flyer_cli.EXIT_USAGE, code)

        self.assertEqual(0, self.run_cli("remove", "--node", PAGE2)[0])
        code, _out, err = self.run_cli("remove", "--node", PAGE1)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-PAGES", err)

    def test_moving_blocks(self):
        self.assertEqual(0, self.run_cli("move", "--node", PHOTO, "--into", PCOL3, "--position", "0")[0])
        self.assertEqual(PHOTO, self.children(PCOL3)[0])
        self.assertEqual(0, self.run_cli("move", "--node", LOGO, "--before", NAME)[0])
        self.assertEqual([LOGO, NAME, ADDRESS], self.children(HCOL1))
        self.assertValid()

        before = self.raw()
        code, _out, err = self.run_cli("move", "--node", PCOL1, "--into", PAGE1)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-WITHIN", err)
        self.assertEqual(before, self.raw())
        code, _out, err = self.run_cli("move", "--node", PROW1, "--into", NCOL1)
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("inside itself", err)
        code, _out, err = self.run_cli("move", "--node", ROOT, "--into", PCOL3)
        self.assertEqual(flyer_cli.EXIT_USAGE, code)

    def test_the_columns_of_a_row_share_it(self):
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", PCOL1, "--key", "width", "--value", "60")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("add up to 102%", err)
        self.assertEqual(before, self.raw())

        self.assertEqual(0, self.run_cli("set", "--node", PROW1, "--key", "widths", "--value", "70, 30")[0])
        self.assertEqual((70, 30), (self.settings(PCOL1)["width"], self.settings(PCOL2)["width"]))
        self.assertEqual(0, self.run_cli("set", "--node", PROW1, "--key", "widths", "--value", "auto, 30%")[0])
        self.assertNotIn("width", self.settings(PCOL1))
        self.assertEqual(30, self.settings(PCOL2)["width"])
        code, _out, err = self.run_cli("set", "--node", PROW1, "--key", "widths", "--value", "50")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("2 columns", err)
        code, _out, _err = self.run_cli("set", "--node", HROW, "--key", "widths", "--value", "50, 60")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertEqual(0, self.run_cli("unset", "--node", PROW1, "--key", "widths")[0])
        self.assertNotIn("width", self.settings(PCOL2))
        self.assertValid()

    def test_a_logos_image_and_its_source_change_together(self):
        self.assertEqual(0, self.run_cli("set", "--node", LOGO, "--key", "media_id", "--value", "6543")[0])
        self.assertEqual("media", self.settings(LOGO)["source"])
        self.assertEqual(6543, self.settings(LOGO)["media_id"])
        self.assertValid()
        self.assertEqual(0, self.run_cli("set", "--node", LOGO, "--key", "source", "--value", "site_logo")[0])
        self.assertNotIn("media_id", self.settings(LOGO))
        self.assertValid()
        code, _out, err = self.run_cli("set", "--node", LOGO, "--key", "source", "--value", "media")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("--key media_id", err)
        self.assertEqual(0, self.run_cli("set", "--node", LOGO, "--key", "media_id", "--value", "12")[0])
        self.assertEqual(0, self.run_cli("unset", "--node", LOGO, "--key", "media_id")[0])
        self.assertNotIn("source", self.settings(LOGO))
        self.assertValid()

    # -- geometry ----------------------------------------------------------------

    def test_an_edit_that_leaves_a_fixed_height_no_room_is_refused(self):
        before = self.raw()
        # The header is 110 px high: 51 + 51 of padding leave it 8.
        code, _out, err = self.run_cli("set", "--node", HEADER, "--key", "band_padding", "--value", "51px 0")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-VALUE", err)
        self.assertIn('crecs_flyer_header "height" leaves less than 10 px', err)
        self.assertIn("2 px short", err)
        self.assertEqual(before, self.raw())
        self.assertEqual(0, self.run_cli("set", "--node", HEADER, "--key", "band_padding", "--value", "50px 0")[0])
        code, _out, err = self.run_cli("set", "--node", HEADER, "--key", "height", "--value", "109")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("1 px short", err)
        # A photo, and a row of fixed height.
        self.assertEqual(0, self.run_cli("set", "--node", PHOTO, "--key", "height", "--value", "40")[0])
        code, _out, err = self.run_cli("set", "--node", PHOTO, "--key", "photo_padding", "--value", "16px 0")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn('crecs_flyer_photo "height"', err)
        code, _out, err = self.run_cli("set", "--node", NROW, "--key", "row_border_width", "--value", "20px 0")
        self.assertEqual(0, code, err)
        code, _out, err = self.run_cli("set", "--node", NROW, "--key", "height", "--value", "49")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn('crecs_flyer_row "height"', err)
        self.assertEqual(0, self.run_cli("set", "--node", NROW, "--key", "height", "--value", "auto")[0])
        self.assertValid()

    def test_an_edit_that_leaves_a_page_too_little_room_is_refused(self):
        for node, key, value in ((HEADER, "height", "250"), (FOOTER, "height", "200"),
                                 (PAGE1, "body_padding", "100px 24px")):
            self.assertEqual(0, self.run_cli("set", "--node", node, "--key", key, "--value", value)[0], key)
        # 250 + 200 + 200 = 650 (the footer's border is inside its height): 80 more of the
        # flyer's padding is 730.
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", ROOT, "--key", "page_padding", "--value", "40px 0")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("take 730 px of the 816 px a landscape page is high", err)
        self.assertIn("[%s]" % PAGE1, err)
        self.assertNotIn("[%s]" % PAGE2, err)
        self.assertEqual(before, self.raw())
        self.assertEqual(0, self.run_cli("set", "--node", ROOT, "--key", "page_padding", "--value", "32px 0")[0])
        # 714: 102 px left. A band's own padding and border are inside its height and take
        # nothing more, so they are no trouble here (the footer keeps 19 of its 200).
        self.assertEqual(0, self.run_cli("set", "--node", FOOTER, "--key", "band_padding", "--value", "90px 0")[0])
        # A portrait flyer is held to the landscape page all the same.
        self.assertEqual(0, self.run_cli("orientation", "portrait")[0])
        code, _out, err = self.run_cli("set", "--node", PAGE1, "--key", "body_border_width", "--value", "2px 0")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("take 718 px", err)
        self.assertValid()

    def test_an_edit_that_crowds_a_row_past_the_narrowest_page_is_refused(self):
        code, out, _err = self.run_cli("--json", "add", "--type", "row", "--into", PAGE2, "--columns", "9")
        self.assertEqual(0, code)
        row = json.loads(out)["node"]
        # 9 x 40 + 8 x 57 = 816: exactly a portrait page.
        self.assertEqual(0, self.run_cli("set", "--node", row, "--key", "gap", "--value", "57")[0])
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", row, "--key", "gap", "--value", "58")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("need 824 px, more than a portrait page's 816 px width", err)
        self.assertEqual(before, self.raw())
        code, _out, err = self.run_cli("add", "--type", "column", "--into", row)
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("The 10 columns of this row", err)
        self.assertEqual(before, self.raw())
        self.assertValid()

    def test_a_hex_colour_with_alpha_and_a_size_with_extra_keys_are_refused(self):
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", NAME, "--key", "name_color", "--value", "#0a3d6280")
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("rgba(10, 61, 98, 0.502)", err)
        code, _out, err = self.run_cli("set", "--node", NAME, "--key", "name_font_size",
                                       "--value", '{"unit": "px", "size": 14, "sizes": []}')
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn('not "sizes"', err)
        self.assertEqual(before, self.raw())
        self.assertEqual(0, self.run_cli("set", "--node", NAME, "--key", "name_color",
                                         "--value", "rgba(10, 61, 98, 0.502)")[0])
        self.assertValid()

    def test_a_geometry_refusal_is_mended_a_step_at_a_time(self):
        def sides(v):
            return {"unit": "px", "top": v, "right": 0, "bottom": v, "left": 0}
        doc = self.doc()
        find(doc, ROOT)[0]["settings"]["page_padding"] = sides(100)
        find(doc, ROOT)[0]["settings"]["page_border_width"] = sides(20)
        find(doc, HEADER)[0]["settings"] = {"height": 250, "band_padding": sides(10)}
        find(doc, FOOTER)[0]["settings"] = {"height": 200, "band_padding": sides(30)}
        find(doc, PAGE2)[0]["settings"]["body_padding"] = sides(20)
        self.write(doc)
        # 240 + 250 + 200 = 690 (the bands' padding is inside them), and 32 more on the
        # first page, 40 on the second: both pages are short.
        out = self.run_cli("validate")[1]
        self.assertIn("take 722 px", out)
        self.assertIn("take 730 px", out)

        code, _out, err = self.run_cli("set", "--node", HEADER, "--key", "height", "--value", "240")
        self.assertEqual(0, code, err)
        self.assertIn("written, but the plugin would still refuse", err)
        self.assertIn("take 720 px", err)
        self.assertNotIn("take 712 px", err)
        before = self.raw()
        code, _out, err = self.run_cli("set", "--node", HEADER, "--key", "height", "--value", "245")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertEqual(before, self.raw())
        self.assertEqual(0, self.run_cli("set", "--node", ROOT, "--key", "page_padding", "--value", "50px 0")[0])
        self.assertValid()

        # A fixed height short of room: a little more height, a little less padding.
        doc = self.doc()
        find(doc, HEADER)[0]["settings"] = {"height": 40, "band_padding": sides(20)}
        self.write(doc)
        self.assertIn("10 px short", self.run_cli("validate")[1])
        code, _out, err = self.run_cli("set", "--node", HEADER, "--key", "height", "--value", "45")
        self.assertEqual(0, code, err)
        self.assertIn("5 px short", err)
        code, _out, err = self.run_cli("set", "--node", HEADER, "--key", "band_padding", "--value", "21px 0")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertEqual(0, self.run_cli("set", "--node", HEADER, "--key", "band_padding", "--value", "15px 0")[0])
        self.assertValid()

    # -- checking ----------------------------------------------------------------

    def test_validate_reports_what_the_plugin_would_refuse(self):
        code, out, _err = self.run_cli("validate")
        self.assertEqual(0, code)
        self.assertIn("valid", out)
        doc = self.doc()
        doc["content"][0]["elements"] = [n for n in doc["content"][0]["elements"] if n["id"] != FOOTER]
        self.write(doc)
        code, out, _err = self.run_cli("validate")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertIn("E-FL-REQUIRED", out)
        self.assertTrue(blocking(self.vocab.check(doc)))

    def test_a_design_already_refused_is_mended_a_step_at_a_time(self):
        doc = self.doc()
        root = doc["content"][0]
        for n in range(4):
            extra = copy.deepcopy(find(doc, PAGE2)[0])
            for node, *_ in flyer_layout.walk({"content": [extra]}):
                node["id"] = "x%d%s" % (n, node["id"][2:])
            root["elements"].append(extra)
        self.write(doc)
        self.assertIn("has 6 page blocks", self.run_cli("validate")[1])

        code, _out, err = self.run_cli("remove", "--node", PAGE2)
        self.assertEqual(0, code)
        self.assertIn("written, but the plugin would still refuse", err)
        self.assertIn("has 5 page blocks", err)
        before = self.raw()
        code, _out, _err = self.run_cli("add", "--type", "page")
        self.assertEqual(flyer_cli.EXIT_REFUSED, code)
        self.assertEqual(before, self.raw())
        code, _out, err = self.run_cli("remove", "--node", "x0ge0002")
        self.assertEqual(0, code)
        self.assertNotIn("still refuse", err)
        self.assertValid()

    # -- reading -----------------------------------------------------------------

    def test_blocks_lists_every_block(self):
        code, out, _err = self.run_cli("--json", "blocks")
        self.assertEqual(0, code)
        self.assertEqual(list(self.vocab.blocks), [row["type"] for row in json.loads(out)])
        code, out, _err = self.run_cli("blocks")
        for block_type in self.vocab.blocks:
            self.assertIn(block_type, out)

    def test_show_the_tree_and_one_block(self):
        code, out, _err = self.run_cli("show")
        self.assertEqual(0, code)
        self.assertIn("Header band", out)
        self.assertIn(PAGE2, out)
        self.assertIn("landscape", out)
        code, out, _err = self.run_cli("--json", "show", "--node", FACTS)
        detail = json.loads(out)
        self.assertEqual(["facts", "label", "value"], list(detail["parts"]))
        self.assertEqual(["total_sf", "sf_available", "rates"], detail["options"]["fields"]["value"])
        self.assertEqual(2, detail["options"]["columns"]["default"])
        self.assertEqual("Asking rate", detail["texts"]["rates"])
        self.assertEqual("Building Size", detail["texts"]["total_sf"])
        code, out, _err = self.run_cli("show", "--node", PHOTO)
        self.assertIn("options:", out)

    def test_controls_says_what_each_setting_takes(self):
        code, out, _err = self.run_cli("--json", "controls", "--node", PHOTO)
        self.assertEqual(0, code)
        rows = {row["name"]: row for row in json.loads(out)}
        self.assertEqual("number 1..30", rows["index"]["allowed"])
        self.assertEqual(1, rows["index"]["value"])
        code, out, _err = self.run_cli("--json", "controls", "--node", PHOTO, "--match", "photo_")
        self.assertTrue(all(row["name"].startswith("photo_") for row in json.loads(out)))

    # -- the file ----------------------------------------------------------------

    def test_the_file_can_come_from_the_environment(self):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {flyer_cli.FILE_ENV: self.path}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = flyer_cli.main(["validate"])
        self.assertEqual(0, code, err.getvalue())

    def test_other_files_are_refused_with_the_right_tool_named(self):
        self.write({"type": "crecs-search-layout", "version": 1, "content": []})
        code, _out, err = self.run_cli("show")
        self.assertEqual(flyer_cli.EXIT_FILE, code)
        self.assertIn("crecs_search.py", err)
        self.write({"version": "0.4", "type": "page", "content": []})
        code, _out, err = self.run_cli("show")
        self.assertEqual(flyer_cli.EXIT_FILE, code)
        self.assertIn("crecs_template.py", err)
        code, _out, err = self.run_cli("show", path=os.path.join(self.dir, "missing.json"))
        self.assertEqual(flyer_cli.EXIT_FILE, code)
        self.assertIn("new --from", err)

    def test_an_export_payload_is_read_as_its_document(self):
        self.write({"document": sample_document(), "manifest": {"kind": "flyer"}})
        self.assertEqual(0, self.run_cli("validate")[0])

    def with_builtins(self, builtins):
        data = copy.deepcopy(self.vocab.data)
        data["builtins"] = builtins
        return mock.patch.object(flyer_cli.Vocabulary, "load", return_value=Vocabulary(data))

    def test_new_from_a_built_in_design(self):
        target = os.path.join(self.dir, "new.json")
        with self.with_builtins({"classic-landscape": sample_document()}):
            code, _out, err = self.run_cli("new", "--from", "classic-landscape", path=target)
            self.assertEqual(0, code, err)
            with open(target, encoding="utf-8") as fh:
                self.assertEqual(normalise(sample_document()), json.load(fh))
            code, _out, err = self.run_cli("new", "--from", "classic-landscape", path=target)
            self.assertEqual(flyer_cli.EXIT_USAGE, code)
            self.assertIn("already exists", err)
            code, _out, err = self.run_cli("new", "--from", "classic-landscape", "--title", "Ours",
                                           "--force", path=target)
            self.assertEqual(0, code, err)
            with open(target, encoding="utf-8") as fh:
                self.assertEqual("Ours", json.load(fh)["title"])
            code, _out, err = self.run_cli("new", "--from", "glossy", path=target)
            self.assertEqual(flyer_cli.EXIT_USAGE, code)
            self.assertIn("classic-landscape", err)

    def test_new_without_built_in_designs(self):
        with self.with_builtins({}):
            code, _out, err = self.run_cli("new", "--from", "classic-landscape",
                                           path=os.path.join(self.dir, "new.json"))
        self.assertEqual(flyer_cli.EXIT_USAGE, code)
        self.assertIn("no built-in designs", err)

    def test_any_text_prints_through_a_pipe_that_is_not_utf8(self):
        # Windows gives a piped stdout its ANSI code page, which has no emoji: printing a
        # person's text must not crash, and the assistant reads the pipe as UTF-8.
        self.assertEqual(0, self.run_cli("text", "--node", TEXT, "--slot", "text",
                                         "--value", "Tours \U0001F600 → now")[0])
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", newline="\n")
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(io.StringIO()):
            code = flyer_cli.main(["--file", self.path, "show", "--node", TEXT])
        stream.flush()
        self.assertEqual(0, code)
        self.assertIn('text text: "Tours \U0001F600 → now"', raw.getvalue().decode("utf-8"))

    def test_nothing_here_reaches_the_network(self):
        network = re.compile(r"^\s*(?:import|from)\s+(?:urllib|http|socket|ssl|requests)\b", re.MULTILINE)
        for path in (os.path.join(SCRIPTS, "crecs_flyer.py"),
                     os.path.join(SCRIPTS, "crecs", "flyer_cli.py"),
                     os.path.join(SCRIPTS, "crecs", "flyer_layout.py")):
            with open(path, encoding="utf-8") as fh:
                self.assertIsNone(network.search(fh.read()), path)


class Reference(unittest.TestCase):

    def test_the_reference_is_the_plugins(self):
        with open(REFERENCE, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn("Generated by the CRE Cloud Solutions plugin", data["_comment"])
        self.assertEqual({"type": "crecs-flyer-layout", "version": 1,
                          "keys": ["type", "version", "title", "content"]}, data["document"])
        self.assertEqual(["id", "elType", "widgetType", "settings", "elements"], data["node_keys"])
        self.assertEqual({"slider": ["unit", "size"],
                          "dimensions": ["unit", "top", "right", "bottom", "left", "isLinked"]}, data["value_keys"])
        self.assertEqual({"landscape": [1056, 816], "portrait": [816, 1056]}, data["page_boxes"])

    def test_the_assistants_reference_names_every_block_and_code(self):
        with open(MARKDOWN, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("Generated by the CRE Cloud Solutions plugin", text)
        vocab = Vocabulary.load()
        for block_type in vocab.blocks:
            self.assertIn("`%s`" % block_type, text)
        for code in CODES:
            self.assertIn("`%s`" % code, text)
        for name in vocab.builtins:
            self.assertIn(name, text)

    def test_the_assistants_reference_says_the_rules_a_person_meets(self):
        with open(MARKDOWN, encoding="utf-8") as fh:
            text = fh.read()
        address = text[text.index("### Address"):text.index("### Badge")]
        self.assertIn("prints only the city, state and zip, never the street", address)
        badge = text[text.index("### Badge"):text.index("### Photo ")]
        self.assertIn("`property_type` the property type's name", badge)
        # Colours: hex alpha is named only to say it is refused.
        self.assertNotRegex(text, r"a colour: `#rgb`, `#rrggbb`, `#rrggbbaa`")
        self.assertIn("not `#rgba` or `#rrggbbaa`", text)
        # The sizes that must add up, with the plugin's own numbers.
        self.assertIn("A page's body keeps at least 100 pixels of a landscape page's 816", text)
        self.assertIn("A fixed height keeps at least 10 pixels for what it holds", text)
        self.assertIn("Each column needs at least 40 pixels", text)
        self.assertIn("The padding and border of `band`, top and bottom, come out of it", text)
        # Two levels of rows nest in a column; the second's columns stay empty.
        self.assertIn("that second nested row's columns are at the limit and must stay empty", text)
        self.assertNotIn("one level down", text)


if __name__ == "__main__":
    unittest.main()
