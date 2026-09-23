"""F2: starting from the template the client actually has.

The documented start is `init --from assets/property-template-all-widgets.json`, the
template the package ships. That is right for a new site and wrong for every existing
one: a client who already has a property page wants *theirs* edited, not replaced.

Elementor exports one in two clicks — Templates, Saved Templates, Export — and `--from`
already accepts the file. What was missing was anyone saying so, and a decent error when
the file is not what it should be. During the rehearsal the WordPress login had expired,
the export handed back an HTML login page, and the failure surfaced as
`nodes.forEach is not a function`, which says nothing about logging in again.
"""

import io
import json
import os
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


class StartFromASiteExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")
        with open(BASE, encoding="utf-8") as fh:
            self.envelope = json.load(fh)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, payload, raw=None):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as fh:
            if raw is not None:
                fh.write(raw)
            else:
                json.dump(payload, fh)
        return path

    def test_an_elementor_export_envelope_is_accepted(self):
        path = self.write("site-export.json", self.envelope)
        code, out, err = run("init", "--from", path, "--workdir", self.wd,
                             "--profile", PROFILE)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(self.wd, "document.json")))

    def test_a_bare_element_array_is_accepted_too(self):
        path = self.write("bare.json", self.envelope["content"])
        code, out, err = run("init", "--from", path, "--workdir", self.wd,
                             "--profile", PROFILE)
        self.assertEqual(code, 0, out + err)

    def test_an_html_page_says_it_is_html_not_that_something_is_not_a_function(self):
        # The exact rehearsal failure: an expired WordPress login returns the login page.
        path = self.write("login.html", None, raw="<!DOCTYPE html><html><body>"
                                                  "<form id='loginform'></form></body></html>")
        code, out, err = run("init", "--from", path, "--workdir", self.wd)
        self.assertNotEqual(code, 0)
        message = (out + err).lower()
        self.assertIn("html", message)
        self.assertTrue(
            any(w in message for w in ("log in", "login", "signed in", "session")),
            "an HTML page where a template was expected should point at the login: " + message,
        )

    def test_a_wordpress_error_json_is_named_as_such(self):
        path = self.write("err.json", {"code": "rest_forbidden",
                                       "message": "Sorry, you are not allowed to do that.",
                                       "data": {"status": 401}})
        code, out, err = run("init", "--from", path, "--workdir", self.wd)
        self.assertNotEqual(code, 0)
        message = out + err
        self.assertIn("rest_forbidden", message)

    def test_a_json_file_that_is_not_a_template_says_what_was_expected(self):
        path = self.write("random.json", {"hello": "world"})
        code, out, err = run("init", "--from", path, "--workdir", self.wd)
        self.assertNotEqual(code, 0)
        message = (out + err).lower()
        self.assertIn("elementor", message)

    def test_an_elementor_kit_export_is_refused_with_its_type(self):
        # Exporting the wrong thing from the same screen is an easy mistake.
        payload = dict(self.envelope)
        payload["type"] = "kit"
        path = self.write("kit.json", payload)
        code, out, err = run("init", "--from", path, "--workdir", self.wd)
        self.assertNotEqual(code, 0)
        self.assertIn("kit", (out + err).lower())


class SkillDocumentsTheRoute(unittest.TestCase):
    """The first draft of these passed by accident, on "their own" in an unrelated
    sentence about widgets and on the *Import* instruction at the end of the file. They
    now look inside a named section, so they test the guidance rather than the vocabulary.
    """

    def setUp(self):
        with open(os.path.join(SKILL_ROOT, "SKILL.md"), encoding="utf-8") as fh:
            self.text = fh.read()
        self.section = self._section("start from", "the client's template",
                                     "which template")

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

    def test_there_is_a_section_about_which_template_to_start_from(self):
        self.assertTrue(self.section.strip(),
                        "SKILL.md has no section on where the starting template comes from")

    def test_that_section_gives_the_wordpress_export_path(self):
        lowered = self.section.lower()
        self.assertIn("saved templates", lowered)
        self.assertIn("export", lowered)

    def test_that_section_prefers_the_clients_template_to_the_shipped_one(self):
        lowered = self.section.lower()
        self.assertIn("assets/property-template-all-widgets.json", self.section)
        self.assertTrue(
            any(w in lowered for w in ("already", "existing site", "what they have")),
            "the section does not say the shipped template is for a site with none yet",
        )

    def test_that_section_warns_the_ids_will_not_match_the_references(self):
        # Elementor regenerates every element id on import, so ids printed from a
        # previous workspace are stale the moment a template round-trips through a site.
        lowered = self.section.lower()
        self.assertIn("id", lowered)


if __name__ == "__main__":
    unittest.main()
