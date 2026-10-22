"""What SKILL.md tells the assistant about the flyer (skill 1.4.0).

The flyer is the last thing the skill learned to design, and the one a person cannot look at
without the assistant's help: the exact PDF is made by CRE Cloud's printer, and the assistant
reads it as pictures of its pages. So the section is held to what it has to carry: the way in,
the tool and the reference to read first, what can and cannot be asked for, the loop that ends
with the assistant looking at the pages itself, the things a real flyer does that a design does
not control, and what sending it is: a button only a person presses in the preview window,
after which the assistant asks CRE Cloud, with a command that cannot send, how it went.

Like test_plain_language, these cannot prove the assistant obeys the file. They prove the
instruction exists where it is read, that the commands it names are real, and that nothing it
says to the person is technical.
"""

import contextlib
import io
import os
import re
import unittest

import crecs_preview
from crecs import flyer_cli

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")

FONTS = ("Lato", "DejaVu Sans", "DejaVu Serif", "Nimbus Sans L", "Nimbus Roman No9 L",
         "URW Gothic L", "URW Bookman L", "URW Palladio L", "Century Schoolbook L")

HEADINGS = ("### What a flyer is", "### Start", "### What they can ask for", "### The flyer's map",
            "### What it can never do", "### The loop", "### Things to know",
            "### Sending the flyer")


def read_skill():
    with open(SKILL_MD, encoding="utf-8") as fh:
        return fh.read()


def body_of(text, heading, level="## "):
    """From `heading` up to the next heading of the same level, or the end."""
    start = text.index(heading)
    end = text.find("\n" + level, start + len(heading))
    return text[start:end if end != -1 else len(text)]


class FlyerSection(unittest.TestCase):

    def setUp(self):
        self.text = read_skill()
        self.assertIn("\n## The flyer\n", self.text, "SKILL.md has no flyer section")
        self.section = body_of(self.text, "## The flyer")
        self.flat = " ".join(self.section.split())

    def part(self, heading):
        return " ".join(body_of(self.section, heading, "### ").split())

    # -- where it is, and what it holds ---------------------------------------------------

    def test_it_follows_the_search_page_and_comes_before_the_rules(self):
        search = self.text.index("\n## The search page\n")
        flyer = self.text.index("\n## The flyer\n")
        rules = self.text.index("\n## The rules that actually break things\n")
        self.assertLess(search, flyer)
        self.assertLess(flyer, rules)

    def test_it_has_the_parts_a_search_page_section_has_in_this_order(self):
        positions = [self.section.find(h + "\n") for h in HEADINGS]
        self.assertNotIn(-1, positions, "a part is missing: " + str(
            [h for h, p in zip(HEADINGS, positions) if p == -1]))
        self.assertEqual(sorted(positions), positions)

    def test_it_says_what_a_flyer_is_and_that_one_design_serves_the_site(self):
        part = self.part("### What a flyer is")
        self.assertIn("whole site", part)
        self.assertIn("one property only", part)
        self.assertIn("Send", part, "it does not say when a design for one property can be saved")
        self.assertIn("1 to 4", part)
        self.assertIn("attachment", part)

    def test_a_design_for_one_property_is_chosen_when_they_press_send(self):
        part = self.part("### What a flyer is")
        self.assertIn("chosen when they press **Send**", part)
        self.assertIn("*Sending the flyer*", part)
        self.assertNotIn("not there yet", part)
        self.assertNotIn("design for the whole site meanwhile", part)

    # -- the way in --------------------------------------------------------------------

    def test_the_person_starts_it_in_template_preview_and_the_assistant_connects(self):
        part = self.part("### Start")
        self.assertIn("Template preview", part)
        self.assertIn("Start flyer preview", part)
        self.assertIn("crecs_preview.py connect", part)
        self.assertIn("-flyer", part, "it does not say the flyer's session file has its own name")
        self.assertIn("crecs_preview.py current", part)
        self.assertIn("crecs_flyer.py", part)

    def test_the_opening_steps_know_the_flyer_too(self):
        opening = body_of(self.text, "## Start here, before anything else")
        self.assertIn("Start flyer preview", opening)
        self.assertIn("preview-<site>-flyer.json", opening)
        self.assertIn("-search.json", opening)
        self.assertIn("flyer", self.text[:self.text.index("## The customer")])

    # -- the tool and the reference ---------------------------------------------------------

    def test_it_names_the_tool_and_the_reference_to_read_before_the_first_edit(self):
        self.assertIn("scripts/crecs_flyer.py", self.flat)
        self.assertIn("references/flyer/FLYER-LAYOUT.md", self.flat)
        read_first = self.flat.index("references/flyer/FLYER-LAYOUT.md")
        self.assertIn("first edit", self.flat[read_first - 160:read_first + 160])

    def test_what_it_calls_the_tool_is_real(self):
        parser = flyer_cli.build_parser()
        choices = set()
        for action in parser._actions:
            if getattr(action, "choices", None) and hasattr(action, "_name_parser_map"):
                choices = set(action.choices)
        self.assertIn("validate", choices)
        used = set(re.findall(r"crecs_flyer\.py(?: --file \S+)? ([a-z][a-z-]*)", self.section))
        self.assertTrue(used, "the section shows no crecs_flyer.py command")
        self.assertEqual(set(), used - choices, "the section names a command the tool does not have")

    def test_the_pdf_command_is_documented_with_options_it_has(self):
        with contextlib.redirect_stdout(io.StringIO()) as help_text:
            with self.assertRaises(SystemExit):
                crecs_preview.main(["pdf", "--help"])
        for option in re.findall(r"crecs_preview\.py pdf((?: --[a-z-]+)*)", self.section):
            for flag in option.split():
                self.assertIn(flag, help_text.getvalue(), "the section names %s, which pdf lacks" % flag)
        for flag in ("--revision", "--dpi", "--out-dir", "--with-pdf", "--fresh"):
            self.assertIn(flag, help_text.getvalue())
            self.assertIn(flag, self.section, "the loop's command line does not show %s" % flag)

    # -- what can and cannot be asked for -------------------------------------------------------

    def test_what_they_can_ask_for(self):
        part = self.part("### What they can ask for")
        for word in ("landscape", "portrait", "header", "footer", "photo", "facts", "suites",
                     "contacts", "map", "logo", "disclaimer", "colours", "up to 4"):
            self.assertIn(word, part, "what they can ask for does not mention %s" % word)

    # -- what the flyer can show of the property: every block has a plain word ------------------------

    # How a person calls each block the flyer has, as the section says it. A block in the vocabulary
    # that is in neither this table nor ARRANGEMENT fails the test below, so a block the plugin
    # gains cannot reach the skill without a word in SKILL.md.
    ARRANGEMENT = {"crecs_flyer", "crecs_flyer_header", "crecs_flyer_footer", "crecs_flyer_page",
                   "crecs_flyer_row", "crecs_flyer_column"}
    PLAIN_NAMES = {
        "crecs_flyer_name": "property's name", "crecs_flyer_headline": "headline",
        "crecs_flyer_address": "address", "crecs_flyer_badge": "labels for its type",
        "crecs_flyer_photo": "one photo", "crecs_flyer_photo_grid": "grid of photos",
        "crecs_flyer_facts": "the facts", "crecs_flyer_highlights": "highlights",
        "crecs_flyer_features": "features", "crecs_flyer_description": "the description",
        "crecs_flyer_suites": "table of suites", "crecs_flyer_traffic": "traffic counts",
        "crecs_flyer_demographics": "demographics", "crecs_flyer_contacts": "the contacts",
        "crecs_flyer_map": "map", "crecs_flyer_logo": "the logo",
        "crecs_flyer_company": "company's name, phone and email", "crecs_flyer_text": "their own text",
        "crecs_flyer_disclaimer": "the disclaimer", "crecs_flyer_divider": "dividing line",
        "crecs_flyer_spacer": "blank space",
    }

    @staticmethod
    def vocabulary():
        from crecs.flyer_layout import Vocabulary
        return Vocabulary.load()

    def test_every_block_the_flyer_has_is_named_in_plain_words_in_what_they_can_ask_for(self):
        vocab = self.vocabulary()
        part = self.part("### What they can ask for").lower()
        unnamed = set(vocab.blocks) - self.ARRANGEMENT - set(self.PLAIN_NAMES)
        self.assertEqual(set(), unnamed, "a block the flyer has, with no plain word in this test or in SKILL.md")
        self.assertEqual(set(), (set(self.PLAIN_NAMES) | self.ARRANGEMENT) - set(vocab.blocks),
                         "a block this test names is gone from the vocabulary")
        for block_type, phrase in self.PLAIN_NAMES.items():
            self.assertIn(phrase, part, "what they can ask for does not name %s as %r" % (block_type, phrase))

    def test_the_new_blocks_are_told_with_the_limits_the_plugin_gives_them(self):
        vocab = self.vocabulary()
        part = self.part("### What they can ask for")
        for block_type, control, words in (("crecs_flyer_features", "max", "40"),
                                           ("crecs_flyer_traffic", "max_rows", "four"),
                                           ("crecs_flyer_demographics", "max_rows", "four")):
            top = vocab.controls(block_type)[control]["max"]
            self.assertEqual(words, {4: "four", 40: "40"}.get(top, str(top)),
                             "%s now allows %s rows: the section has to say so" % (block_type, top))
            self.assertIn("up to %s rows" % words, part)
        suites = vocab.controls("crecs_flyer_suites")
        self.assertEqual(20, suites["max_rows"]["max"])
        self.assertEqual(10, suites["max_rows"]["default"])
        self.assertIn("up to 10 rows, or up to 20 when it lists every suite", part)

    def test_the_new_blocks_have_the_words_the_plugin_prints_in_them(self):
        vocab = self.vocabulary()
        part = self.part("### What they can ask for")
        for block_type in ("crecs_flyer_traffic", "crecs_flyer_demographics"):
            for control in ("text_year_label", "text_source_label"):
                self.assertIn('"%s"' % vocab.controls(block_type)[control]["default"], part,
                              "the list of words does not give %s's %s" % (block_type, control))
        self.assertIn("label and its value", part)

    def test_the_suites_table_can_list_every_suite_with_a_status_column(self):
        vocab = self.vocabulary()
        suites = vocab.controls("crecs_flyer_suites")
        self.assertEqual(["vacant", "all"], suites["filter"]["options"])
        self.assertEqual("vacant", suites["filter"]["default"], "the section says the available ones are the default")
        self.assertIn("status", suites["columns"]["options"])
        available = suites["text_status_vacant"]["default"]
        leased = suites["text_status_occupied"]["default"]
        part = self.part("### What they can ask for")
        self.assertIn("**Status** column that says %s or %s" % (available, leased), part)
        self.assertIn("lists every suite, leased ones too", part)
        self.assertIn("A leased suite never shows its rate", part)
        self.assertIn("no tenant, rent or lease date is ever printed", part)
        self.assertIn("its Status words too", part)

    def test_the_two_new_facts_are_named(self):
        vocab = self.vocabulary()
        facts = vocab.controls("crecs_flyer_facts")
        self.assertTrue({"land_sf", "property_class"} <= set(facts["fields"]["options"]))
        self.assertEqual("Land Size", facts["text_land_sf"]["default"])
        self.assertEqual("Class", facts["text_property_class"]["default"])
        self.assertIn("land size, class", self.part("### What they can ask for"))

    def test_a_block_with_nothing_to_show_prints_nothing_and_the_person_is_told_it_is_not_broken(self):
        part = self.part("### What they can ask for")
        self.assertIn("A block with nothing to show prints nothing", part)
        self.assertIn("set in CRE Cloud not to show it on the flyer", part)
        self.assertIn("not think it is broken", part)
        self.assertIn("look at a property that has the data", part)
        self.assertIn("features, traffic counts or demographics it lacks", self.part("### The loop"))

    def test_a_long_table_is_checked_in_the_exact_pdf_and_never_squeezed_with_a_smaller_font(self):
        part = self.part("### Things to know")
        self.assertIn("A long table may not fit its page", part)
        self.assertIn("The exact PDF (`pdf`) is how to check that a long table fits the page", part)
        self.assertIn("plenty of data", part)
        self.assertIn("never a smaller font", part)
        self.assertIn("pdf", self.preview_commands(), "the command the section names for the exact PDF is gone")

    def test_the_ready_made_designs_have_none_of_the_new_blocks_and_the_section_says_so(self):
        from crecs import flyer_layout
        new = {"crecs_flyer_features", "crecs_flyer_traffic", "crecs_flyer_demographics"}
        builtins = self.vocabulary().builtins
        self.assertTrue(builtins)
        for name, document in builtins.items():
            used = {node["widgetType"] for node, *_ in flyer_layout.walk(document)}
            self.assertEqual(set(), used & new, "%s has a block the section says the ready-made designs lack" % name)
        self.assertIn("ready-made designs have no features, traffic counts or demographics",
                      self.part("### Start"))

    def test_what_they_can_ask_for_puts_no_block_id_or_setting_in_front_of_the_assistants_customer(self):
        part = self.part("### What they can ask for")
        self.assertNotRegex(part, r"crecs_flyer_|land_sf|property_class|max_rows|turn_off|\bfilter\b")

    # -- the map: street, satellite, satellite with street names, and what only the exact PDF shows ----------

    # How a person calls each setting of the Map block that is not its look. A setting the plugin gains
    # that is not here fails the first test below, so it cannot reach the skill without plain words.
    MAP_OPTIONS = {"height": "map's height", "map_type": "street map", "boundaries": "boundaries",
                   "zoom": "how close it is"}
    MAP_KINDS = {"road": "street map", "satellite": "satellite map", "hybrid": "satellite map with street names"}

    def map_part(self):
        return self.part("### The flyer's map")

    def test_every_setting_of_the_map_block_has_plain_words_in_the_map_part(self):
        controls = self.vocabulary().controls("crecs_flyer_map")
        options = {name for name, spec in controls.items() if spec.get("group") == "option"}
        self.assertEqual(set(), options - set(self.MAP_OPTIONS), "a setting of the Map block with no plain word here")
        self.assertEqual(set(), set(self.MAP_OPTIONS) - options, "a setting this test names is gone from the block")
        part = self.map_part()
        for name, phrase in self.MAP_OPTIONS.items():
            self.assertIn(phrase, part, "the section does not say %s as %r" % (name, phrase))

    def test_the_map_part_sits_between_what_they_can_ask_for_and_what_it_can_never_do(self):
        asking = self.section.index("### What they can ask for\n")
        never = self.section.index("### What it can never do\n")
        mapped = self.section.index("### The flyer's map\n")
        self.assertLess(asking, mapped)
        self.assertLess(mapped, never)
        self.assertIn("*The flyer's map*", self.part("### What they can ask for"),
                      "what they can ask for does not point at it")

    def test_the_map_can_be_a_street_map_a_satellite_map_or_a_satellite_map_with_street_names(self):
        controls = self.vocabulary().controls("crecs_flyer_map")
        self.assertEqual(["road", "satellite", "hybrid"], controls["map_type"]["options"])
        self.assertEqual(set(self.MAP_KINDS), set(controls["map_type"]["options"]),
                         "a kind of map the plugin has needs plain words here")
        self.assertEqual("road", controls["map_type"]["default"])
        part = self.map_part()
        for kind, phrase in self.MAP_KINDS.items():
            self.assertIn(phrase, part, "the map part does not call %s %r" % (kind, phrase))
        self.assertRegex(part, r"street map\*\* — the default", "it does not say the street map is the default")
        self.assertIn("always works", part)

    def test_boundaries_and_what_is_drawn_on_the_property_show_on_a_satellite_map_only(self):
        controls = self.vocabulary().controls("crecs_flyer_map")
        self.assertEqual(["off", "on"], controls["boundaries"]["options"])
        self.assertEqual("off", controls["boundaries"]["default"], "the section says boundaries are asked for")
        part = self.map_part()
        for phrase in ("property's boundaries", "drawn on the property in CRE Cloud",
                       "A street map cannot show them", "offer a satellite map",
                       "the satellite kind first, then the boundaries", "Nothing extra appears"):
            self.assertIn(phrase, part, "the map part does not say: " + phrase)

    def test_the_zoom_is_told_as_the_plugin_has_it(self):
        zoom = self.vocabulary().controls("crecs_flyer_map")["zoom"]
        self.assertEqual((1, 21), (zoom["min"], zoom["max"]))
        self.assertNotIn("default", zoom, "the section says that, with no number, the property's own zoom is used")
        part = self.map_part()
        self.assertIn("from 1 (the most land) to 21 (the closest)", part)
        for phrase in ("smaller number shows more land", "same number shows the same area",
                       "whatever size the map has on the page", "change the number, not the box",
                       "zoom saved with the property in CRE Cloud"):
            self.assertIn(phrase, part, "the map part does not say: " + phrase)

    def test_a_property_that_hides_its_address_shows_no_map_of_any_kind(self):
        part = self.map_part()
        self.assertIn("hides its address shows no map of any kind", part)
        self.assertIn("on purpose", part)
        notes = self.part("### Things to know")
        self.assertIn("has no map", notes)
        self.assertIn("whatever kind of map", notes)

    def test_a_satellite_map_is_offered_only_after_the_capabilities_line_says_it_can_be_made(self):
        part = self.map_part()
        self.assertIn("`crecs_preview.py capabilities --base <site>`", part)
        self.assertIn("Before you offer one", part)
        self.assertLess(part.index("Before you offer one"), part.index("It lists satellite maps"))
        for phrase in ("*street map only*", "*not known*", "line is missing", "satellite maps are not available",
                       "offer the street map", "ask for it to be updated"):
            self.assertIn(phrase, part, "the map part does not say: " + phrase)
        self.assertIn("capabilities", self.preview_commands())

    def test_the_capabilities_words_the_section_quotes_are_the_commands_own(self):
        part = self.map_part()
        said = {"*street map only*": crecs_preview.map_types_words(["road"]),
                "*not known*": crecs_preview.map_types_words(None)}
        for quoted, words in said.items():
            self.assertIn(quoted, part)
            self.assertTrue(words.startswith(quoted.strip("*")), "the command no longer says %s" % quoted)
        every = crecs_preview.map_types_words(["road", "satellite", "hybrid"])
        self.assertTrue(every.startswith("available"), every)
        for phrase in self.MAP_KINDS.values():
            self.assertIn(phrase, every)

    def test_the_refusal_of_an_aerial_map_is_covered_and_matches_the_command(self):
        part = self.map_part()
        for phrase in ("refused when the PDF is made", "nothing was made or sent", "put the street map back"):
            self.assertIn(phrase, part, "the map part does not say: " + phrase)
        words = crecs_preview._explain("crecs_preview_flyer_map_unsupported", "", 422)
        self.assertIn("cannot make an aerial map", words)
        self.assertIn("nothing was made or sent", crecs_preview.REFUSAL_HINTS["crecs_preview_flyer_map_unsupported"])

    def test_the_aerial_map_shows_only_in_the_exact_pdf_and_the_pages_view_is_told_truthfully(self):
        # The Pages view is the HTML CRE Cloud is sent, unchanged: the map is an image with no picture
        # in it until CRE Cloud puts one in when it prints, for the street map too.
        part = self.map_part()
        for phrase in ("only in the exact PDF", "**Exact PDF**", "**Pages** view", "empty box",
                       "for the street map too", "never judge a map", "open the page pictures first"):
            self.assertIn(phrase, part, "the map part does not say: " + phrase)
        self.assertNotIn("Pages view shows the map as", part)

    def test_the_loop_looks_for_a_street_map_where_a_satellite_one_was_designed(self):
        loop = self.part("### The loop")
        self.assertIn("a map that is missing, or is the street map where a satellite one was designed", loop)

    def test_each_map_warning_is_explained_in_one_line_and_in_the_commands_own_words(self):
        part = self.map_part()
        said = (("*showing the street map instead*", {"code": "W-FL-MAP-FALLBACK", "reason": "no_key"}),
                ("*could not be drawn on the map*", {"code": "W-FL-MAP-OVERLAY-SKIPPED", "skipped": 3}),
                ("*hides its address*", {"code": "W-FL-NO-MAP", "reason": "address_hidden"}))
        for quoted, warning in said:
            self.assertIn(quoted, part, "the map part does not explain " + quoted)
            self.assertIn(quoted.strip("*"), crecs_preview.warning_words(warning),
                          "the command no longer says " + quoted)
        # The reasons the fallback gives, each as the command words it.
        for phrase, reason in (("has no map key", "no_key"), ("Google", "google_error"),
                               ("ran out of time", "timeout"),
                               ("no satellite pictures of that place at that zoom", "no_imagery")):
            self.assertIn(phrase, part, "the map part does not give the reason: " + phrase)
            self.assertIn(phrase, crecs_preview.warning_words({"code": "W-FL-MAP-FALLBACK", "reason": reason}))
        self.assertIn("smaller zoom number", part)
        self.assertIn("not what they designed", part)

    def test_the_map_part_puts_no_id_code_or_setting_name_in_front_of_the_person(self):
        part = self.map_part()
        self.assertNotRegex(part, r"crecs_flyer_|map_type|W-FL-|flyer_map_types|address_hidden|no_imagery|"
                                  r"google_error|no_key|crecs_preview_flyer|\bfilter\b")
        replies = [l for l in body_of(self.section, "### The flyer's map", "### ").splitlines()
                   if l.strip().startswith(">")]
        self.assertGreaterEqual(len(replies), 2, "the map part has no example replies")
        joined = " ".join(replies).lower()
        self.assertIn("satellite", joined)
        self.assertIn("street map", joined)

    def test_the_fonts_are_the_printers_and_arial_is_not_one(self):
        part = self.part("### What they can ask for")
        for font in FONTS:
            self.assertIn(font, part, "the list of fonts lacks %s" % font)
        arial = [s for s in re.split(r"(?<=[.!?])\s+", part) if "Arial" in s]
        self.assertTrue(arial, "nothing says what to do when they ask for Arial")
        self.assertTrue(any(w in " ".join(arial) for w in ("no ", "not ", "cannot", "never")),
                        "Arial is mentioned without saying it is not available")

    def test_what_it_can_never_do(self):
        part = self.part("### What it can never do")
        for word in ("HTML", "CSS", "font", "shadow", "SVG", "do not promise"):
            self.assertIn(word, part, "the limits do not mention %s" % word)
        self.assertIn("never fake", part.lower())

    # -- the loop, ending with the assistant looking ---------------------------------------------

    def test_the_loop_ends_with_the_assistant_looking_at_the_pages_itself(self):
        loop = self.part("### The loop")
        order = [loop.find(word) for word in ("crecs_flyer.py", "validate", "apply", "crecs_preview.py pdf",
                                              "page-")]
        self.assertNotIn(-1, order)
        self.assertEqual(sorted(order), order, "the loop's steps are not in order")
        for phrase in ("yourself", "overflow", "attachment pages", "header and footer"):
            self.assertIn(phrase, loop, "the loop does not mention %s" % phrase)
        self.assertTrue(any(w in loop for w in ("image-reading", "open each page")),
                        "it does not say to open the page pictures")

    def test_it_asks_for_a_check_on_another_property_when_the_design_depends_on_data(self):
        loop = self.part("### The loop")
        self.assertIn("another property", loop)

    def test_nothing_is_called_right_before_the_pictures_have_been_looked_at(self):
        loop = self.part("### The loop")
        self.assertIn("never tell them", loop)

    # -- things a real flyer does -------------------------------------------------------------------

    def test_the_notes(self):
        part = self.part("### Things to know")
        self.assertIn("city, state and zip", part)
        self.assertIn("no map", part)
        self.assertIn("own orientation", part)
        self.assertIn("IABS", part)
        self.assertIn("end", part)
        self.assertIn("frame", part)

    # -- who may use it, and what limits a design --------------------------------------------------------

    def test_a_flyer_preview_needs_a_site_administrator_and_the_person_is_asked_to_sign_in_as_one(self):
        part = self.part("### Start")
        self.assertIn("needs a site administrator", part)
        self.assertIn("administrator account", part)
        self.assertIn("sign in", part)
        self.assertIn("Start flyer preview", part)
        # The plain statement to the person is an example reply, so it cannot carry a code.
        replies = [l for l in body_of(self.section, "### Start", "### ").splitlines()
                   if l.strip().startswith(">")]
        self.assertTrue(any("site administrator" in l for l in replies),
                        "there is no example reply telling a person to sign in as an administrator")

    def test_the_other_refusals_of_a_flyer_preview_are_covered(self):
        part = self.part("### Start")
        self.assertIn("at most three flyer previews", part)
        self.assertIn("close one", part)
        self.assertIn("not on the site's list", part)

    def test_a_design_has_at_most_two_logos_each_about_300_kb(self):
        part = self.part("### What it can never do")
        self.assertIn("At most two logos", part)
        self.assertIn("300 KB", part)
        self.assertIn("a third", part)
        asking = self.part("### What they can ask for")
        self.assertIn("at most two logos", asking)

    def test_a_logo_that_is_too_big_is_left_out_and_the_person_is_asked_for_a_smaller_one(self):
        part = self.part("### Things to know")
        self.assertIn("left out", part)
        self.assertIn("300 KB", part)
        self.assertIn("nothing in the summary says so", part)
        self.assertIn("upload a smaller picture", part)
        self.assertIn("crecs_preview.py media", part)
        self.assertIn("too much image data", part)
        loop = self.part("### The loop")
        self.assertIn("a logo whose picture is too big", loop, "the look-over does not mention a missing logo")

    def test_a_fresh_pdf_is_for_when_something_changed_in_cre_cloud_and_not_by_default(self):
        loop = self.part("### The loop")
        self.assertIn("`--fresh`", loop)
        self.assertIn("When to ask for a fresh PDF", loop)
        for phrase in ("new attachment", "something like that changed", "reads the property anew",
                       "Do not use it otherwise", "not for the first PDF you make in a conversation"):
            self.assertIn(phrase, loop, "the loop does not say: %s" % phrase)
        # The design's own changes need nothing: a new revision is always a new PDF.
        self.assertIn("always makes a new PDF", loop)

    def test_the_age_of_a_pdf_is_passed_on_in_plain_words(self):
        loop = self.part("### The loop")
        self.assertIn("how old the PDF is", loop)
        self.assertIn("over a minute", loop)
        self.assertIn("minutes ago", loop)
        self.assertIn("did not make a new PDF", loop)

    def test_the_hours_allowance_is_not_waited_for_and_the_person_is_told_plainly(self):
        loop = self.part("### The loop")
        self.assertIn("hour's allowance", loop)
        self.assertIn("do not run it again and again", loop)
        self.assertIn("do not wait for it", loop)
        self.assertIn("A busy printer is different", loop)
        replies = [l for l in body_of(self.section, "### The loop", "### ").splitlines()
                   if l.strip().startswith(">")]
        self.assertTrue(any("shared" in l for l in replies), "there is no example reply for the hour's allowance")

    def test_what_the_section_says_matches_what_the_tool_does(self):
        # The sentences above name a refusal, a flag and a limit: each must be real.
        from crecs.flyer_layout import Vocabulary
        vocab = Vocabulary.load()
        self.assertEqual(2, vocab.limits["max_logos"], "the section says two logos")
        self.assertEqual(2, vocab.blocks["crecs_flyer_logo"]["max"])
        words = crecs_preview._explain("crecs_preview_forbidden", "Previewing a flyer needs a WordPress administrator", 403)
        self.assertIn("site administrator", words)
        self.assertIn("administrator account", words)
        self.assertIn("smaller logo", crecs_preview._explain("crecs_preview_flyer_too_large", "x", 413))

    # -- sending: a person's button, and the assistant asks afterwards ---------------------------------

    def sending(self):
        return self.part("### Sending the flyer")

    @staticmethod
    def preview_commands():
        """The commands crecs_preview.py has, from its own help."""
        with contextlib.redirect_stdout(io.StringIO()) as help_text:
            with contextlib.suppress(SystemExit):
                crecs_preview.main(["--help"])
        # The usage line lists --kind's choices before the commands': take the one with the commands.
        lists = [m.split(",") for m in re.findall(r"\{([a-z,]+)\}", help_text.getvalue())]
        return set([names for names in lists if "capabilities" in names][0])

    def test_sending_is_no_longer_called_unavailable(self):
        self.assertNotIn("not available yet", self.sending())
        self.assertNotIn("not there yet", self.flat, "a part of the section still says sending is not there")
        self.assertNotIn("which is not there", self.flat)

    def test_the_person_presses_send_chooses_and_confirms_in_the_bar_in_that_order(self):
        part = self.sending()
        for phrase in ("**Send**", "preview window", "Use it for the whole site",
                       "Use it only for this property", "confirm", "bar"):
            self.assertIn(phrase, part, "the way to send does not mention " + phrase)
        order = [part.index(p) for p in ("**Send**", "Use it for the whole site", "confirm")]
        self.assertEqual(sorted(order), order, "the steps of sending are not in the order a person meets them")
        self.assertIn("buttons' names as the screen shows them", part)

    def test_the_assistant_never_sends_and_has_nothing_to_send_with(self):
        part = self.sending()
        self.assertIn("Never send, publish or export a flyer yourself", part)
        self.assertIn("browser you can drive", part)
        self.assertIn("nothing you can run sends", part)
        self.assertIn("never from a command", part)

    def test_only_a_site_administrator_can_send(self):
        part = self.sending()
        self.assertIn("Only a site administrator can send", part)
        self.assertIn("missing or grey", part)
        self.assertIn("signed in", part)

    def test_the_two_choices_are_explained_in_plain_words_before_they_press(self):
        part = self.sending()
        whole = part[part.index("whole site"):]
        for phrase in ("from now on", "every property of the site",
                       "refreshes the flyers of the properties that already have one by itself",
                       "a few every day, the oldest first", "over the next days, not at once"):
            self.assertIn(phrase, whole, "the whole-site choice does not say: " + phrase)
        for phrase in ("its own design", "every other property keeps the site's design",
                       "go back to the site's design"):
            self.assertIn(phrase, part, "the one-property choice does not say: " + phrase)

    def test_visitors_keep_getting_todays_flyer_until_a_send_finishes(self):
        part = self.sending()
        self.assertIn("keep getting the flyer they get today", part)
        self.assertIn("until a send has finished", part)

    def test_after_they_say_they_sent_it_the_assistant_asks_with_sent(self):
        part = self.sending()
        self.assertIn("Check, never assume", part)
        self.assertIn("crecs_preview.py sent --session-file <file>", part)
        self.assertLess(part.index("Check, never assume"), part.index("crecs_preview.py sent"))
        self.assertIn("When they say they sent it", part)

    def test_nothing_is_called_live_before_sent_says_it_is_ready(self):
        part = self.sending()
        self.assertIn("never tell them it is live", part)
        self.assertIn("only after `sent` says CRE Cloud made it", part)
        self.assertIn("never because they pressed the button", part)

    def test_each_answer_of_sent_has_its_plain_words_and_they_are_the_commands_own(self):
        # The section quotes how each answer begins, so that what the assistant reads here and
        # what the command prints cannot drift apart.
        part = self.sending()
        answers = {
            "not sent": ({"sent": False, "state": None},
                         "Nothing has been sent to CRE Cloud for this property yet"),
            "ready": ({"sent": True, "state": "ready", "up_to_date": True}, "CRE Cloud made the flyer"),
            "making": ({"sent": True, "state": "rendering"}, "CRE Cloud is still making it"),
            "retrying": ({"sent": True, "state": "queued", "retrying": True},
                         "CRE Cloud had a problem and is trying again"),
            "failed": ({"sent": True, "state": "failed"}, "CRE Cloud could not make the flyer"),
            "newer": ({"sent": True, "state": "ready", "up_to_date": False},
                      "What is on screen in the preview is newer than what was sent"),
        }
        for name, (answer, lead) in answers.items():
            with self.subTest(answer=name):
                self.assertIn("*" + lead, part, "the section does not quote how this answer begins")
                self.assertIn(lead, crecs_preview.sent_text(dict(answer, property="x")),
                              "the command no longer says what the section quotes")

    def test_the_section_says_what_to_do_about_each_answer(self):
        part = self.sending()
        for phrase in ("If it was not sent", "If CRE Cloud is still making it", "If CRE Cloud is trying again",
                       "If CRE Cloud could not make it", "If what is on screen is newer",
                       "keep designing", "press **Send** again", "previous flyer"):
            self.assertIn(phrase, part, "the section does not say: " + phrase)

    def test_the_warnings_of_a_sent_flyer_are_passed_on_in_plain_words(self):
        part = self.sending()
        self.assertIn("warnings", part)
        self.assertIn("plain words", part)
        self.assertIn("picture could not be loaded", part)

    def test_a_site_without_the_send_button_is_told_plainly_and_capabilities_is_how_to_tell(self):
        part = self.sending()
        self.assertIn("crecs_preview.py capabilities --base <site>", part)
        self.assertIn("flyer_send", part)
        self.assertIn("older", part)
        self.assertIn("update", part)

    def test_there_are_example_replies_to_say_how_to_send_and_what_came_of_it(self):
        replies = [l for l in body_of(self.section, "### Sending the flyer", "### ").splitlines()
                   if l.strip().startswith(">")]
        joined = " ".join(replies)
        self.assertGreaterEqual(len(replies), 6)
        self.assertIn("Send", joined)
        self.assertIn("whole site", joined)
        self.assertIn("administrator", joined)

    def test_every_preview_command_the_section_names_is_a_real_one(self):
        commands = self.preview_commands()
        used = set(re.findall(r"crecs_preview\.py ([a-z][a-z-]*)", self.section))
        self.assertIn("sent", used)
        self.assertEqual(set(), used - commands, "the section names a command crecs_preview.py lacks")
        for name in commands:
            self.assertFalse("send" in name, "a command that could send: " + name)

    def test_the_sent_command_is_documented_with_options_it_has(self):
        with contextlib.redirect_stdout(io.StringIO()) as help_text:
            with contextlib.suppress(SystemExit):
                crecs_preview.main(["sent", "--help"])
        for option in re.findall(r"crecs_preview\.py sent((?: --[a-z-]+)*)", self.section):
            for flag in option.split():
                self.assertIn(flag, help_text.getvalue(), "the section names %s, which sent lacks" % flag)

    def test_what_the_section_says_about_sending_matches_what_the_tool_does(self):
        words = crecs_preview.warning_words({"code": "W-FL-IMAGE-LOAD"})
        self.assertIn("picture could not be loaded", words)
        self.assertIn("missing or broken in the flyer", words)
        self.assertIn("picture could not be loaded", self.sending())

    # -- nothing technical goes to the person ---------------------------------------------------------

    def test_no_example_reply_in_the_section_hands_the_person_a_technical_word(self):
        quoted = "\n".join(l for l in self.section.splitlines() if l.strip().startswith(">"))
        self.assertTrue(quoted.strip(), "the section has no example reply")
        for bad in ("crecs_", "token", "session file", "--", "terminal", ".json", "widgetType", "__dynamic__"):
            self.assertNotIn(bad, quoted, "an example reply to the person contains %r" % bad)
        self.assertEqual([], re.findall(r"\b[0-9a-f]{7,8}\b", quoted))

    def test_the_audience_rule_is_kept(self):
        self.assertIn("Plain language", self.text)
        self.assertIn("Never put an id in front of them", self.text)
        part = self.part("### The loop")
        self.assertIn("plain words", part)


class WhereItIsMentioned(unittest.TestCase):

    def setUp(self):
        self.text = read_skill()

    def test_the_description_mentions_the_flyer_and_still_fits(self):
        match = re.match(r"---\n(.*?)\n---\n", self.text, re.S)
        description = [l for l in match.group(1).splitlines() if l.startswith("description:")][0]
        value = description.partition(":")[2].strip()
        self.assertIn("flyer", value)
        self.assertLessEqual(len(value), 200)

    def test_the_intro_points_at_the_flyer_section(self):
        intro = self.text[:self.text.index("## The customer")]
        self.assertIn("The flyer", intro)

    def test_the_layout_of_the_skill_lists_the_flyer_files(self):
        layout = body_of(self.text, "## Layout of this skill")
        for path in ("references/flyer/FLYER-LAYOUT.md", "references/flyer/flyer-layout.json",
                     "scripts/crecs_flyer.py"):
            self.assertIn(path, layout)
        preview_line = [l for l in layout.splitlines() if "crecs_preview.py" in l][0]
        self.assertIn("pdf", preview_line)
        self.assertIn("sent", preview_line)

    def test_the_preview_connection_text_names_every_sessions_file(self):
        step = body_of(self.text, "**3. Open that site's preview yourself.**", "## ")
        self.assertIn("-flyer", step)


if __name__ == "__main__":
    unittest.main()
