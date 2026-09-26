"""The frontmatter and the guided design start, which were added together in 1.1.0.

The frontmatter is checked because claude.ai rejects an upload whose description runs
past 200 characters, and nothing else in the suite would notice: the other surfaces
allow 1024, so a long description passes everywhere until a client tries to upload it.

The guided start is the part of SKILL.md a client with no support person walks through,
so it is held to the same rules as the rest: no id is asked of the person, anything read
from another website is data rather than instructions, and the step numbers the prose
refers to are the step numbers on the page.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")

DESCRIPTION_LIMIT = 200  # claude.ai; Claude Code, Codex and ChatGPT allow 1024


def read_skill():
    with open(SKILL_MD, encoding="utf-8") as fh:
        return fh.read()


def frontmatter(text):
    match = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def section(text, heading):
    """Body under the first heading containing `heading`, up to the next heading of
    the same or a higher level."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("#") and heading in line.lower():
            level = len(line) - len(line.lstrip("#"))
            body = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("#") and len(nxt) - len(nxt.lstrip("#")) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


def sentences(text):
    flat = " ".join(text.split())
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]


class Frontmatter(unittest.TestCase):
    def setUp(self):
        self.fields = frontmatter(read_skill())

    def test_the_name_is_the_folder_name(self):
        self.assertEqual(os.path.basename(SKILL_ROOT), self.fields.get("name"))

    def test_the_description_fits_claude_ai(self):
        description = self.fields.get("description", "")
        self.assertTrue(description, "SKILL.md has no description")
        self.assertLessEqual(
            len(description), DESCRIPTION_LIMIT,
            "description is %d characters; claude.ai refuses the upload past %d"
            % (len(description), DESCRIPTION_LIMIT))

    def test_the_description_is_a_valid_plain_yaml_scalar(self):
        # An unquoted value may not contain ": " or " #"; either turns the line into
        # something other than one string and the skill fails to load.
        description = self.fields.get("description", "")
        self.assertNotIn(": ", description)
        self.assertNotIn(" #", description)


class GuidedStart(unittest.TestCase):
    def setUp(self):
        self.text = read_skill()
        self.guided = section(self.text, "guided design start")

    def test_there_is_a_guided_start(self):
        self.assertTrue(self.guided.strip(), "SKILL.md has no guided design start")

    def test_the_logo_step_asks_the_person_for_no_id(self):
        logo = section(self.guided, "logo")
        self.assertTrue(logo.strip(), "the guided start has no logo step")
        # The person doing something with an id, in that order: "they ... note the
        # attachment id", "ask them for the id". "Add the id where they want it" is
        # the assistant's work and does not count.
        handles = r"\b(note|copy|find|send|tell|give|paste|share|look up|write down)\b"
        asked = [s for s in sentences(logo)
                 if re.search(r"\b(they|them)\b[^.]*" + handles + r"[^.]*\bids?\b", s, re.I)
                 or re.search(r"\bask\b[^.]*\bids?\b", s, re.I)]
        self.assertEqual([], asked,
                         "the logo step puts an id on the person: %s" % asked)

    def test_a_website_read_for_inspiration_is_data_not_instructions(self):
        websites = section(self.guided, "websites")
        self.assertTrue(websites.strip(), "the guided start has no websites step")
        lower = " ".join(websites.lower().split())
        self.assertIn("data", lower)
        self.assertTrue(
            any(w in lower for w in ("never instructions", "never as instructions",
                                     "not instructions", "never follow",
                                     "do not follow")),
            "nothing says to ignore instructions found on another site")

    def test_the_intro_names_the_steps_the_page_actually_numbers(self):
        numbers = [int(n) for n in re.findall(r"^### (\d+)\.", self.guided, re.M)]
        self.assertTrue(numbers, "the guided start has no numbered steps")
        self.assertEqual(list(range(numbers[0], numbers[0] + len(numbers))), numbers,
                         "the guided steps are not numbered consecutively")
        intro = self.guided.split("###", 1)[0]
        self.assertIn("steps %d to %d" % (numbers[0], numbers[-1]), intro,
                      "the intro does not say which steps follow")

    def test_the_opening_runs_straight_into_the_guided_steps(self):
        opening = section(self.text, "start here")
        opened = [int(n) for n in re.findall(r"^\*\*(\d+)\.", opening, re.M)]
        guided = [int(n) for n in re.findall(r"^### (\d+)\.", self.guided, re.M)]
        self.assertTrue(opened and guided)
        self.assertEqual(opened[-1] + 1, guided[0],
                         "the opening ends at %d but the guided start begins at %d"
                         % (opened[-1], guided[0]))


if __name__ == "__main__":
    unittest.main()
