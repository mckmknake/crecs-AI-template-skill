"""The first four things the skill does, before any editing.

Asked for directly: begin by asking which WordPress site this is, open a browser at it
so the person can sign in, open that site's preview screen, and never open a real
property page.

The last one is the rule that matters. A live property URL renders the *published*
template, so an edit in progress is not on it: someone looking at that page sees the
site as it is today and can easily believe they are looking at their change. It is also
the client's live site, being loaded to look at work that is not there.

Two things constrain how this is written. The skill runs on surfaces that have no
browser at all, so the instruction has to say what to do when there is none rather than
stall. And the preview needs the plugin's preview module enabled on that site, which
most client sites will not have on day one — so "open the preview" needs a stated path
for when there is no preview to open.
"""

import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")


class OpeningSequence(unittest.TestCase):
    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.text = fh.read()
        self.lower = self.text.lower()
        self.section = self._section("start here", "first", "opening")

    def _section(self, *titles):
        lines = self.text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("#") and any(t in line.lower() for t in titles):
                body = []
                for nxt in lines[i + 1:]:
                    if nxt.startswith("#"):
                        break
                    body.append(nxt)
                return "\n".join(body)
        return ""

    def test_there_is_an_opening_section(self):
        self.assertTrue(self.section.strip(), "SKILL.md has no opening sequence")

    def test_it_comes_before_everything_else(self):
        idx = self.lower.index(self.section.strip().splitlines()[0].lower()[:40])
        for later in ("## the loop", "## plain language", "## which template"):
            pos = self.lower.find(later)
            if pos != -1:
                self.assertLess(idx, pos, "the opening sequence sits after " + later)

    # -- the four steps --------------------------------------------------------

    def test_step_one_asks_which_wordpress_site(self):
        body = self.section.lower()
        self.assertIn("which", body)
        self.assertIn("wordpress", body)
        self.assertIn("site", body)

    def test_step_two_opens_a_browser_for_the_person_to_sign_in(self):
        body = self.section.lower()
        self.assertTrue(
            any(w in body for w in ("browser", "open the site")),
            "nothing says to open the site",
        )
        self.assertTrue(
            any(w in body for w in ("sign in", "log in", "login")),
            "nothing says the person signs in",
        )

    def test_it_never_asks_for_the_password_itself(self):
        body = self.section.lower()
        self.assertTrue(
            any(w in body for w in ("never ask", "do not ask", "their own", "they sign in")),
            "the section must be explicit that the person signs in, not the assistant",
        )

    def test_step_three_opens_the_preview_screen(self):
        body = self.section.lower()
        self.assertIn("template preview", body)

    def test_step_four_forbids_opening_a_real_property_page(self):
        body = self.section.lower()
        self.assertTrue(
            any(w in body for w in ("never open", "do not open", "never load")),
            "the prohibition is not stated",
        )
        self.assertTrue(
            "/property/" in self.section or "property page" in body,
            "it does not say which page is forbidden",
        )

    def test_the_prohibition_says_why(self):
        body = self.section.lower()
        self.assertTrue(
            any(w in body for w in ("published", "live", "not your change", "as it is today")),
            "the rule is given without the reason, so it reads as arbitrary",
        )

    # -- and it does not stall when the ground is missing -----------------------

    def test_it_says_what_to_do_with_no_browser(self):
        body = self.section.lower()
        self.assertTrue(
            any(w in body for w in ("no browser", "cannot open", "without a browser")),
            "the skill runs where there is no browser; the section must handle that",
        )

    def test_it_says_what_to_do_when_the_site_has_no_preview(self):
        body = self.section.lower()
        self.assertTrue(
            any(w in body for w in ("not enabled", "no preview", "does not have")),
            "most client sites will not have the preview module enabled",
        )

    def test_it_stays_vendor_neutral(self):
        # Delivery 2 required no vendor-exclusive tool in the core; the adapters carry
        # anything specific. Naming one assistant's browser here would break that.
        for name in ("Claude Code", "ChatGPT", "Codex", "claude.ai"):
            self.assertNotIn(name, self.section,
                             "the opening sequence names %s; keep the core neutral" % name)

    def test_no_ids_leak_into_the_opening(self):
        leaked = re.findall(r"\b[0-9a-f]{7,8}\b", self.section)
        self.assertEqual([], leaked, "element ids in the opening: %s" % leaked)


if __name__ == "__main__":
    unittest.main()
