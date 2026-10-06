"""The five ready-made styles in assets/styles/.

Each is a whole property page that ships in every package and that SKILL.md offers as
the usual starting point, so each is held to what the starter is held to
(test_base_template.py) and to what SKILL.md says about it: its fonts, an empty loader
slug so the profile can fill it, and no address of any site in it.

Every case first breaks a copy and requires the check to see it, and only then holds
the shipped file to it. A check that cannot fail proves nothing; test_base_template.py
records how that once happened here.
"""

import copy
import json
import os
import re
import unittest

from crecs import validate
from crecs.catalog import Catalog
from crecs.document import Document
from crecs.profile import Profile
from crecs.state import baseline_keys_of

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
STYLES_DIR = os.path.join(SKILL_ROOT, "assets", "styles")
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")
CATALOG = Catalog.load_default()

STYLES = ("bold", "modern", "classic", "corporate", "minimal")

# The font families SKILL.md's table promises for each style, and nothing else.
FONTS = {
    "bold": {"Oswald", "Inter"},
    "modern": {"Montserrat", "Inter"},
    "classic": {"Playfair Display", "Source Sans 3"},
    "corporate": {"Roboto"},
    "minimal": {"Inter"},
}

# The one error a style may carry, as the starter does: its contact buttons open the
# reference site's popups until step 10 points them at the client's own.
ALLOWED_ERRORS = {"E-DEP-UNRESOLVED"}

ABSOLUTE_URL = re.compile(r"https?://", re.IGNORECASE)
ACTIVE = re.compile(r"<script|javascript:|\beval\s*\(|@import|url\(|expression\(|base64",
                    re.IGNORECASE)


def path_of(style):
    return os.path.join(STYLES_DIR, "property-template-style-%s.json" % style)


def shipped(style):
    with open(path_of(style), encoding="utf-8") as fh:
        return json.load(fh)


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get("elements") or [])


def settings(node):
    return node.get("settings") if isinstance(node.get("settings"), dict) else {}


def errors(payload):
    # As `init` validates a file it imports: what the file already carries is its
    # baseline, so a legacy option value Elementor still reads is a warning, not an error.
    # The starter carries eighteen of those; the styles inherited a few.
    document = Document(payload)
    result = validate.validate(document, CATALOG, Profile.empty(),
                               baseline_keys=baseline_keys_of(document))
    return {f.code for f in result.findings if f.severity == "ERROR"}


def fonts(payload):
    return {value for node in walk(payload["content"])
            for key, value in settings(node).items()
            if key.endswith("font_family") and isinstance(value, str) and value}


def loader_slugs(payload):
    return [settings(n).get("slug") for n in walk(payload["content"])
            if n.get("widgetType") == "crecs_property_data"]


def text(payload):
    return json.dumps(payload, ensure_ascii=False)


def first_widget(payload, widget_type):
    return next(n for n in walk(payload["content"]) if n.get("widgetType") == widget_type)


def section(markdown, heading):
    """One section of SKILL.md: from its heading to the next heading of level 2 or 3."""
    start = markdown.index(heading) + len(heading)
    following = re.search(r"\n#{2,3} ", markdown[start:])
    return markdown[start:start + following.start()] if following else markdown[start:]


def clears_popups_before_export(text):
    """Do the section's commands take the buttons off their popups before exporting?

    The starter's and every style's contact buttons open the reference site's popups,
    and the plugin's preview refuses a page whose buttons open popups the site does not
    have — on every client's site, that is. The tour and the style previews are for
    looking, so the buttons are cleared first.
    """
    clear = text.find("--clear")
    export = text.find("crecs_template.py export")
    return "popup --workdir" in text and clear != -1 and export != -1 and clear < export


class ReadyMadeStyles(unittest.TestCase):

    def test_the_five_styles_and_nothing_else(self):
        expected = {"property-template-style-%s.json" % s for s in STYLES}
        self.assertEqual(expected, set(os.listdir(STYLES_DIR)))
        with open(SKILL_MD, encoding="utf-8") as fh:
            skill = fh.read()
        for style in STYLES:
            with self.subTest(style=style):
                self.assertIn(style.capitalize(), skill, "SKILL.md does not name the %s style" % style)
        self.assertIn("assets/styles/property-template-style-<style>.json", skill)

    # -- each check, proved able to fail -------------------------------------------

    def test_each_check_can_actually_fail(self):
        broken = copy.deepcopy(shipped("bold"))
        elements = list(walk(broken["content"]))
        elements[1]["id"] = elements[0]["id"]
        self.assertTrue(errors(broken) - ALLOWED_ERRORS, "a duplicated id went unseen")

        broken = copy.deepcopy(shipped("bold"))
        first_widget(broken, "heading")["settings"]["title"] = "https://example.test/x"
        self.assertTrue(ABSOLUTE_URL.search(text(broken)), "an address went unseen")

        broken = copy.deepcopy(shipped("bold"))
        first_widget(broken, "heading")["settings"]["custom_css"] = "@import url(x.css);"
        self.assertTrue(ACTIVE.search(text(broken)), "an @import went unseen")

        broken = copy.deepcopy(shipped("bold"))
        first_widget(broken, "crecs_property_data")["settings"]["slug"] = "a-real-slug"
        self.assertNotEqual([""], loader_slugs(broken), "a filled slug went unseen")

        broken = copy.deepcopy(shipped("bold"))
        first_widget(broken, "heading")["settings"]["typography_font_family"] = "Papyrus"
        self.assertNotEqual(FONTS["bold"], fonts(broken), "a stray font went unseen")

    # -- the shipped styles ------------------------------------------------------

    def test_each_validates_as_the_starter_does(self):
        for style in STYLES:
            with self.subTest(style=style):
                self.assertEqual(set(), errors(shipped(style)) - ALLOWED_ERRORS)

    def test_none_names_a_site(self):
        for style in STYLES:
            with self.subTest(style=style):
                with open(path_of(style), encoding="utf-8") as fh:
                    self.assertIsNone(ABSOLUTE_URL.search(fh.read()))

    def test_none_carries_active_content(self):
        for style in STYLES:
            with self.subTest(style=style):
                with open(path_of(style), encoding="utf-8") as fh:
                    found = ACTIVE.search(fh.read())
                self.assertIsNone(found, found.group(0) if found else "")

    def test_each_leaves_the_loader_slug_to_the_profile(self):
        for style in STYLES:
            with self.subTest(style=style):
                self.assertEqual([""], loader_slugs(shipped(style)))

    def test_each_uses_the_fonts_skill_md_promises(self):
        for style in STYLES:
            with self.subTest(style=style):
                self.assertEqual(FONTS[style], fonts(shipped(style)))


LOOK_ONLY = ("### 4. The showcase tour", "### 5. The look they want")


class LookOnlyPreviews(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(SKILL_MD, encoding="utf-8") as fh:
            cls.skill = fh.read()

    def test_the_check_can_fail(self):
        for heading in LOOK_ONLY:
            with self.subTest(step=heading):
                stripped = "\n".join(line for line in section(self.skill, heading).splitlines()
                                     if "popup" not in line)
                self.assertFalse(clears_popups_before_export(stripped))

    def test_the_tour_and_the_styles_take_the_popups_off_first(self):
        for heading in LOOK_ONLY:
            with self.subTest(step=heading):
                self.assertTrue(clears_popups_before_export(section(self.skill, heading)),
                                "the preview refuses this page on any site without the "
                                "reference site's popups")


if __name__ == "__main__":
    unittest.main()
