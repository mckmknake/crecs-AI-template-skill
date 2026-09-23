"""SKILL.md must make the assistant talk to a person, not to a developer.

Rehearsing a client walkthrough exposed this. To get a preview open, the assistant
(me) said "template 4601", "popup 4554", "`__dynamic__`" and "element 7f553b25" out
loud to someone who does not know what any of that is. Nothing in SKILL.md said not to,
and nothing told it to ask "which property page?" and "which property shall we use as
the example?" and resolve the ids underneath.

That is a product defect, not a style preference: the person cannot answer a question
phrased in ids, so the assistant either guesses or stalls.

These assert the instruction exists where the assistant actually reads it. They cannot
assert the assistant obeys — only a real conversation shows that, and the record says
so plainly.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")


class PlainLanguage(unittest.TestCase):
    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.text = fh.read()
        self.lower = self.text.lower()

    def section(self, *titles):
        """Return the body of the first heading whose text contains one of `titles`."""
        lines = self.text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("#") and any(t in line.lower() for t in titles):
                body = []
                for nxt in lines[i + 1:]:
                    if nxt.startswith("#") and not nxt.startswith("#####"):
                        break
                    body.append(nxt)
                return "\n".join(body)
        return ""

    # -- the instruction exists ------------------------------------------------

    def test_there_is_a_section_about_how_to_talk_to_the_person(self):
        body = self.section("plain language", "talking to", "how to ask")
        self.assertTrue(body.strip(), "SKILL.md has no section on how to address the person")

    def test_it_says_not_to_put_ids_in_front_of_the_person(self):
        body = self.section("plain language", "talking to", "how to ask")
        self.assertIn("id", body.lower())
        self.assertTrue(
            any(w in body.lower() for w in ("never", "do not", "don't")),
            "the rule about ids is not stated as a prohibition",
        )

    def test_it_gives_the_two_opening_questions_in_plain_words(self):
        body = self.section("plain language", "talking to", "how to ask").lower()
        # Which page, and which property to show while working on it.
        self.assertIn("which", body)
        self.assertIn("example", body)

    def test_it_names_the_jargon_that_leaked(self):
        # The specific words that went in front of a client. Naming them is what makes
        # the rule checkable rather than a vague plea to be friendly.
        # Whitespace is collapsed first: the requirement is that the rule says these
        # things, not that prose avoids wrapping across a line at an awkward point.
        body = re.sub(r"\s+", " ", self.section("plain language", "talking to", "how to ask"))
        for token in ("__dynamic__", "widgetType", "element id"):
            self.assertIn(token, body, "the rule does not mention %s" % token)

    def test_it_says_to_describe_things_the_way_the_page_shows_them(self):
        body = self.section("plain language", "talking to", "how to ask").lower()
        self.assertTrue(
            any(w in body for w in ("what the visitor sees", "the way the page",
                                    "as it appears", "on the page")),
            "nothing tells the assistant to name things as they appear on the page",
        )

    def test_it_covers_reporting_a_problem_without_ids(self):
        # The live rehearsal found two dead contact buttons. Saying "popup 4554 does not
        # exist" is useless to the person; "your two contact buttons open nothing" is not.
        body = self.section("plain language", "talking to", "how to ask").lower()
        self.assertTrue(
            any(w in body for w in ("symptom", "what is broken", "what they would see",
                                    "what the visitor")),
            "nothing says how to report a problem in the person's terms",
        )

    # -- and it is reachable ---------------------------------------------------

    def test_the_rule_is_near_the_top_not_buried(self):
        idx = self.lower.find("plain language")
        self.assertNotEqual(idx, -1, "the section is missing entirely")
        # Before the command reference, or it gets read too late to matter.
        loop = self.lower.find("## the loop")
        self.assertTrue(0 < idx < loop, "the rule sits after the command loop")

    def test_the_technical_vocabulary_is_still_documented_for_the_assistant(self):
        # The point is not to remove precision from the tool, only from the conversation.
        # Control names and element ids must still be first-class in the instructions.
        self.assertIn("references/widgets/", self.text)
        self.assertIn("--element", self.text)

    def test_the_claim_about_what_is_untested_is_kept(self):
        # An instruction file cannot prove the assistant obeys it.
        body = self.section("plain language", "talking to", "how to ask").lower()
        self.assertTrue(
            any(w in body for w in ("cannot be enforced", "not enforced", "no validator",
                                    "nothing here checks")),
            "the section does not admit that nothing mechanically enforces it",
        )


class NoJargonLeakInExamples(unittest.TestCase):
    """The worked example of a reply must itself be jargon-free."""

    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.text = fh.read()

    def test_the_example_reply_contains_no_widget_type(self):
        # Quoted example replies are marked with '>' blockquotes.
        quoted = "\n".join(l for l in self.text.splitlines() if l.strip().startswith(">"))
        self.assertTrue(quoted.strip(), "there is no example reply to check")
        for bad in ("crecs_property_", "widgetType", "__dynamic__"):
            self.assertNotIn(bad, quoted,
                             "an example reply to the person contains %r" % bad)

    def test_the_example_reply_contains_no_bare_element_id(self):
        quoted = "\n".join(l for l in self.text.splitlines() if l.strip().startswith(">"))
        # Elementor element ids are 7-8 hex characters.
        leaked = re.findall(r"\b[0-9a-f]{7,8}\b", quoted)
        self.assertEqual([], leaked, "element ids leaked into an example reply: %s" % leaked)


if __name__ == "__main__":
    unittest.main()
