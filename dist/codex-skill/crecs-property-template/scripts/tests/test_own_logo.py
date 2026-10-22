"""The client's own logo, as SKILL.md teaches it (skill 1.4.x).

CRE Cloud keeps the client's company logo and flyer logo, and every kind of page can show them
as a variable: a logo changed in CRE Cloud shows by itself, where an uploaded file keeps
showing the old one. These hold SKILL.md to that: the assistant looks at what CRE Cloud keeps
first, uses it in preference to an upload in the logo step of the guided start, in the search
page and in the flyer, says in one plain sentence that it follows a change, and falls back to a
file only when CRE Cloud has none or does not say. The commands it names must be real, and the
words it tells the person must be plain.

Nothing here can show that the assistant obeys; it can show the instruction is where the
assistant reads it, and that it agrees with what the tools print.
"""

import argparse
import os
import re
import unittest

import crecs_preview
from crecs import cli, flyer_cli, search_cli
from crecs.catalog import Catalog

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")

HEADING = "## The client's own logo"


def read_skill():
    with open(SKILL_MD, encoding="utf-8") as fh:
        return fh.read()


def body_of(text, heading, level="## "):
    """From `heading` up to the next heading of the same level, or the end."""
    start = text.index(heading)
    end = text.find("\n" + level, start + len(heading))
    return text[start:end if end != -1 else len(text)]


def flat(text):
    return " ".join(text.split())


def replies(text):
    """The example replies in a piece of SKILL.md: its blockquote lines, without the marks."""
    return "\n".join(re.sub(r"^\s*>\s?", "", l) for l in text.splitlines() if l.strip().startswith(">"))


def subcommands(parser):
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    return {}


class TheSection(unittest.TestCase):

    def setUp(self):
        self.text = read_skill()
        self.assertIn("\n" + HEADING + "\n", self.text, "SKILL.md has no section on the client's own logo")
        self.section = body_of(self.text, HEADING)
        self.flat = flat(self.section)

    def test_it_says_what_is_gained_and_makes_cre_cloud_the_first_choice(self):
        for phrase in ("company logo", "flyer logo", "changes the logo in CRE Cloud",
                       "changes by itself", "a copy"):
            self.assertIn(phrase, self.flat, "the section does not say: " + phrase)
        self.assertIn("use the one in CRE Cloud first, and a file only when it is not there", self.flat)
        for kind in ("the property page", "any other Elementor page", "the search page", "the flyer"):
            self.assertIn(kind, self.flat, "it does not say the rule holds for " + kind)

    def test_it_looks_at_what_cre_cloud_keeps_before_offering_anything(self):
        self.assertIn("Look before you offer it", self.flat)
        self.assertIn("crecs_preview.py capabilities --base <site>", self.flat)
        self.assertLess(self.section.index("capabilities --base"), self.section.index("The property page"),
                        "it tells how to use the logo before telling to look")

    def test_what_it_says_of_each_state_is_what_the_tool_prints(self):
        # The section names the states by the words the `capabilities` line starts with.
        both = crecs_preview.brand_logos_words({"company": True, "flyer": True})
        one = crecs_preview.brand_logos_words({"company": True, "flyer": False})
        none = crecs_preview.brand_logos_words({"company": False, "flyer": False})
        unknown = crecs_preview.brand_logos_words(None)
        for said, bold in ((both, "**Both available, or one only**"), (one, "**Both available, or one only**"),
                           (none, "**None**"), (unknown, "**Not known**")):
            self.assertIn(bold, self.flat, "the section has no entry for a line that reads: " + said[:40])
        self.assertTrue(both.startswith("available"), both)
        self.assertTrue(one.startswith("company logo only"), one)
        self.assertTrue(none.startswith("none"), none)
        self.assertTrue(unknown.startswith("not known"), unknown)
        self.assertIn("no line about logos at all", self.flat, "an older plugin sends no line: it must be covered")

    def test_it_falls_back_to_a_file_only_when_cre_cloud_has_none_or_does_not_say(self):
        none = flat(body_of(self.section, "- **None**", "- **"))
        unknown = flat(body_of(self.section, "- **Not known**", "\n\n"))
        self.assertIn("a file from their computer", none)
        self.assertIn("fall back to a file", unknown)
        self.assertIn("could not confirm it", unknown, "it does not say that the logo could not be confirmed")
        self.assertIn("Never ask them to upload a file for a logo CRE Cloud has", self.flat)

    def test_it_tells_the_person_in_one_sentence_that_it_follows_a_change_and_when(self):
        for phrase in ("follows any change they make in CRE Cloud by itself", "about ten minutes",
                       "keeps its pages in a cache", "when it is sent again",
                       "refreshes it by itself", "a few flyers a day"):
            self.assertIn(phrase, self.flat, "the sentence for the person does not say: " + phrase)

    def test_nothing_promises_a_flyer_follows_a_logo_at_the_daily_refresh_or_within_a_day(self):
        # The plugin refreshes at most 20 designed flyers a day, oldest first, and only when the
        # site's scheduler runs: a flyer follows a changed logo when it is sent again, or when
        # the plugin refreshes it by itself. Neither "the daily refresh" nor "within a day" is true.
        text = flat(read_skill())
        for promise in ("daily refresh", "within a day", "once a day", "at the daily refresh"):
            self.assertNotIn(promise, text, "SKILL.md still promises: " + promise)
        for promise in ("so those change within a day", "rebuilds the flyers of the properties that already have one every day"):
            self.assertNotIn(promise, text, "SKILL.md still promises: " + promise)

    def test_every_command_it_shows_is_real(self):
        parsers = {"template": cli.build_parser(), "search": search_cli.build_parser(),
                   "flyer": flyer_cli.build_parser()}
        used = re.findall(r"crecs_(template|search|flyer)\.py ([a-z-]+)", self.section)
        self.assertEqual({("template", "add-widget"), ("template", "bind"), ("search", "add-block"),
                          ("search", "set"), ("flyer", "set")}, set(used), "the section runs other commands")
        for tool, name in used:
            self.assertIn(name, subcommands(parsers[tool]), "the section runs %s %s, which does not exist" % (tool, name))
        # What it mentions without a full command line.
        self.assertIn("`remove-block`", self.section)
        self.assertIn("remove-block", subcommands(parsers["search"]))
        self.assertIn("`catalog --tags`", self.section)
        self.assertIn("catalog", subcommands(parsers["template"]))
        for flag in ("--tag", "--param", "--control", "--element"):
            self.assertIn(flag, self.section)

    def test_every_tag_and_source_it_names_exists(self):
        catalog = Catalog.load_default()
        for tag in set(re.findall(r"crecs-[a-z]+-logo", self.text)):
            self.assertIn(tag, catalog.bindable_tag_names(), tag + " is named in SKILL.md and not in the catalog")
        for tag in ("crecs-company-logo", "crecs-flyer-logo"):
            self.assertIn(tag, self.section)
        from crecs.flyer_layout import Vocabulary as Flyer
        from crecs.search_layout import Vocabulary as Search
        self.assertEqual(["site_logo", "media", "company_logo", "flyer_logo"],
                         Flyer.load().controls("crecs_flyer_logo")["source"]["options"])
        self.assertEqual(["company_logo", "flyer_logo"],
                         Search.load().controls("crecs_search_logo")["source"]["options"])
        for source in ("company_logo", "flyer_logo", "crecs_search_logo"):
            self.assertIn(source, self.section)
        self.assertEqual((16, 300), (Search.load().controls("crecs_search_logo")["height"]["min"],
                                     Search.load().controls("crecs_search_logo")["height"]["max"]))
        self.assertIn("16 to 300", self.flat)

    def test_the_flyer_logo_is_worded_as_the_api_chooses_it(self):
        self.assertIn("property's own flyer design in CRE Cloud when it has one, otherwise the site's default",
                      self.flat)
        self.assertIn("Only a PNG, JPEG or GIF can be used", self.flat)
        self.assertIn("300 KB and 3000-pixel limits of an uploaded picture do not apply", self.flat)
        self.assertIn("count toward the two logos", self.flat)

    def test_a_logo_that_does_not_show_is_never_fixed_with_a_file_on_the_website(self):
        part = flat(body_of(self.section, "**When a logo kept in CRE Cloud does not show**", "\n\n"))
        self.assertIn("the fix is never a file on the website", part)
        self.assertIn("they change it in CRE Cloud", part)

    def test_the_search_logo_is_told_with_its_places_and_what_it_is_not(self):
        self.assertIn("never in the filters", self.flat)
        self.assertIn("can repeat", self.flat)
        self.assertIn("pin image on the map is a different thing", self.flat)

    def test_the_example_replies_are_plain(self):
        quoted = replies(self.section)
        self.assertTrue(quoted.strip(), "the section has no example reply")
        for bad in ("crecs", "--", "token", "terminal", "session file", "`", "tag", "widget", "block",
                    "bind", "source", "__dynamic__", "http"):
            self.assertNotIn(bad, quoted, "an example reply to the person contains %r" % bad)
        self.assertEqual([], re.findall(r"\b[0-9a-f]{7,8}\b", quoted), "an id leaked into an example reply")
        lowered = flat(quoted).lower()
        for phrase in ("by itself", "ten minutes", "your logo", "png, jpeg or gif", "a few flyers a day"):
            self.assertIn(phrase, lowered, "no example reply says: " + phrase)


class TheLogoStepOfTheGuidedStart(unittest.TestCase):

    def setUp(self):
        self.text = read_skill()
        self.step = flat(body_of(self.text, "### 8. Logo", "### "))

    def test_the_logo_kept_in_cre_cloud_comes_first_and_the_file_is_the_fallback(self):
        used = self.step.index("use the logo CRE Cloud already keeps")
        upload = self.step.index("Media → Add New")
        self.assertLess(used, upload, "the upload is taught before the logo CRE Cloud keeps")
        self.assertIn("Only when CRE Cloud has no company logo, or does not say", self.step)
        self.assertIn("a copy that a later change in CRE Cloud will not reach", self.step)

    def test_it_checks_before_it_offers_and_says_what_to_tell_the_person(self):
        self.assertIn("crecs_preview.py capabilities --base <site>", self.step)
        self.assertIn("follows any change they make in CRE Cloud by itself", self.step)
        self.assertIn("about ten minutes", self.step)
        self.assertIn("keeps its pages in a cache", self.step, "the page's ten minutes holds unless the site caches its pages")
        self.assertIn("nothing to upload", self.step.lower())

    def test_it_names_the_way_to_put_the_logo_on_the_page(self):
        self.assertIn("image` widget", self.step)
        self.assertIn("The client's own logo", self.step)
        self.assertIn("references/widgets/core-image.md", self.step)

    def test_a_site_header_that_already_shows_the_logo_is_still_asked_about_first(self):
        self.assertLess(self.step.index("already shows their logo"), self.step.index("use the logo CRE Cloud"))


class TheOtherSectionsAgree(unittest.TestCase):

    def setUp(self):
        self.text = read_skill()

    def test_the_search_page_offers_the_logo_and_says_it_is_not_the_pin(self):
        search = flat(body_of(self.text, "## The search page"))
        self.assertIn("**Their logo**", search)
        self.assertIn("follows a change they make in CRE Cloud by itself", search)
        self.assertIn("keeps its pages in a cache", search, "the page's ten minutes holds unless the site caches its pages")
        self.assertIn("It is not the map's pin", search)
        self.assertIn("It is a copy: a logo used as a pin does not follow a change made in CRE Cloud", search)
        self.assertIn("add-block | remove-block", search)

    def test_the_flyer_offers_the_logos_kept_in_cre_cloud_and_never_a_file_as_their_fix(self):
        flyer = body_of(self.text, "## The flyer")
        asking = flat(body_of(flyer, "### What they can ask for", "### "))
        self.assertIn("company logo or the flyer logo kept in CRE Cloud", asking)
        self.assertIn("at most two logos", asking)
        never = flat(body_of(flyer, "### What it can never do", "### "))
        self.assertIn("whatever the logos show, the two kept in CRE Cloud included", never)
        self.assertIn("The logos kept in CRE Cloud have no such size limit, but must be PNG, JPEG or GIF", never)
        notes = flat(body_of(flyer, "### Things to know", "### "))
        for phrase in ("A logo kept in CRE Cloud is not a file on the site, so a file is never the fix",
                       "Do not ask the person to upload a smaller picture for it",
                       "they change it in CRE Cloud", "when it is sent again",
                       "refreshes it by itself (a few flyers a day)",
                       "the logo of that property's own flyer design when it has one, otherwise the site's default"):
            self.assertIn(phrase, notes, "the flyer notes do not say: " + phrase)
        self.assertIn("upload a smaller picture", notes, "an uploaded picture still needs a smaller one")
        loop = flat(body_of(flyer, "### The loop", "### "))
        self.assertIn("a logo kept in CRE Cloud that cannot print", loop)

    def test_validation_names_the_errors_a_logo_tag_can_have(self):
        text = flat(body_of(self.text, "## Validation, in three severities"))
        self.assertIn("a CRE Cloud tag that does not exist or sits on a control of another kind", text)

    def test_the_property_page_commands_say_how_to_bind_a_logo(self):
        text = flat(body_of(self.text, "### Bind a property field", "### "))
        self.assertIn("--tag crecs-company-logo", text)
        self.assertIn("catalog --tags", text)
        data = flat(body_of(self.text, "## Binding property data"))
        self.assertIn("settings=\"%7B%7D\"", data)
        self.assertIn("crecs-flyer-logo", data)


if __name__ == "__main__":
    unittest.main()
