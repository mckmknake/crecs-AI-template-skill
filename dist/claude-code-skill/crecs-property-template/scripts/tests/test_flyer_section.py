"""What SKILL.md tells the assistant about the flyer (skill 1.4.0).

The flyer is the last thing the skill learned to design, and the one a person cannot look at
without the assistant's help: the exact PDF is made by CRE Cloud's printer, and the assistant
reads it as pictures of its pages. So the section is held to what it has to carry: the way in,
the tool and the reference to read first, what can and cannot be asked for, the loop that ends
with the assistant looking at the pages itself, the things a real flyer does that a design does
not control, and the plain statement that sending it is not there yet.

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

HEADINGS = ("### What a flyer is", "### Start", "### What they can ask for",
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

    # -- sending is not there yet ---------------------------------------------------------------------

    def test_sending_is_not_available_and_will_be_a_button_for_a_person(self):
        part = self.part("### Sending the flyer")
        self.assertIn("not available yet", part)
        self.assertIn("button", part)
        self.assertIn("preview window", part)
        self.assertIn("keep getting", part)
        self.assertIn("never", part)

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

    def test_the_preview_connection_text_names_every_sessions_file(self):
        step = body_of(self.text, "**3. Open that site's preview yourself.**", "## ")
        self.assertIn("-flyer", step)


if __name__ == "__main__":
    unittest.main()
