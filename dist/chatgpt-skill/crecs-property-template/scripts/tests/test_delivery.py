"""Contract for handing the finished template to the person who asked for it.

The skill could always produce an export, but only onto a filesystem path inside a
workspace the person had to name. That is fine in an editor with a repository open and
useless anywhere else: on a surface with no writable project, `--out` had nowhere to
point, and `--workdir` had to name a directory that the person did not want and did not
know to ask for.

Three things are covered here.

* `--out -` writes the Elementor JSON to stdout, so the file can be produced where
  there is no disk to leave it on. Stdout must carry the JSON and nothing else, or it
  cannot be redirected into a file or attached to a reply.
* `--workdir` may be omitted. The workspace then lives in a stable directory under the
  system temp, so the separate `init`, `set` and `export` processes still find each
  other, and the path is announced rather than guessed at.
* `SKILL.md` says to deliver the file. The scripts producing it is not the same as the
  person receiving it, and an instruction nobody wrote is an instruction nobody
  follows.
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from crecs import cli

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
SCRIPTS = os.path.join(SKILL_ROOT, "scripts")
ENTRY = os.path.join(SCRIPTS, "crecs_template.py")
BASE_TEMPLATE = os.path.join(SKILL_ROOT, "assets", "property-template-all-widgets.json")
PROFILE_FIXTURE = os.path.join(HERE, "fixtures", "target-profile.test.json")
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")

ELEMENTOR_ENVELOPE_KEYS = ["content", "page_settings", "version", "title", "type"]


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cli.main(list(args))
    return code, out.getvalue(), err.getvalue()


class DeliveryCase(unittest.TestCase):
    """A workspace that is ready to export, and an isolated temp home for the default."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")
        # CRECS_WORKDIR is how a caller pins the default somewhere it controls. Setting
        # it here keeps these tests out of the real temp directory, and out of each
        # other's way.
        self.previous_env = os.environ.get(cli.WORKDIR_ENV)
        os.environ[cli.WORKDIR_ENV] = os.path.join(self.tmp, "default-home")
        code, out, err = run_cli("init", "--from", BASE_TEMPLATE, "--workdir", self.wd,
                                 "--profile", PROFILE_FIXTURE)
        self.assertEqual(code, 0, out + err)

    def tearDown(self):
        if self.previous_env is None:
            os.environ.pop(cli.WORKDIR_ENV, None)
        else:
            os.environ[cli.WORKDIR_ENV] = self.previous_env
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestExportToStdout(DeliveryCase):
    def test_stdout_carries_the_elementor_envelope(self):
        code, out, err = run_cli("export", "--workdir", self.wd, "--out", "-")
        self.assertEqual(code, 0, err)
        envelope = json.loads(out)
        self.assertEqual(list(envelope.keys()), ELEMENTOR_ENVELOPE_KEYS)

    def test_stdout_carries_nothing_but_the_envelope(self):
        # Anything else on stdout — a summary line, a warning count — makes the stream
        # unusable as a file, which is the entire point of this mode.
        _, out, _ = run_cli("export", "--workdir", self.wd, "--out", "-")
        json.loads(out)  # would raise on a stray line

    def test_the_summary_goes_to_stderr(self):
        _, out, err = run_cli("export", "--workdir", self.wd, "--out", "-")
        self.assertIn("ready", err.lower())
        self.assertNotIn("ready", out.lower())

    def test_no_file_called_dash_is_created(self):
        # The bug this replaces: `--out -` was taken literally and produced a file
        # named `-` in the current directory.
        before = set(os.listdir(self.tmp))
        run_cli("export", "--workdir", self.wd, "--out", "-")
        self.assertEqual(before, set(os.listdir(self.tmp)))
        self.assertFalse(os.path.exists("-"))

    def test_the_stdout_export_equals_the_file_export(self):
        path = os.path.join(self.tmp, "on-disk.json")
        run_cli("export", "--workdir", self.wd, "--out", path)
        _, out, _ = run_cli("export", "--workdir", self.wd, "--out", "-")
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), json.loads(out))

    def test_json_and_stdout_export_cannot_share_the_stream(self):
        code, out, err = run_cli("export", "--workdir", self.wd, "--out", "-", "--json")
        self.assertNotEqual(code, 0)
        self.assertIn("--json", out + err)

    def test_a_blocked_export_writes_nothing_to_stdout(self):
        # Without the profile the two popup bindings are unresolved, so the export is
        # refused. A refusal must not leave half an envelope on the stream.
        bare = os.path.join(self.tmp, "bare")
        run_cli("init", "--from", BASE_TEMPLATE, "--workdir", bare)
        code, out, err = run_cli("export", "--workdir", bare, "--out", "-")
        self.assertNotEqual(code, 0)
        self.assertEqual(out.strip(), "")
        self.assertIn("refused", err.lower())

    def test_a_draft_to_stdout_is_named_as_a_draft_on_stderr(self):
        bare = os.path.join(self.tmp, "bare2")
        run_cli("init", "--from", BASE_TEMPLATE, "--workdir", bare)
        code, out, err = run_cli("export", "--workdir", bare, "--out", "-",
                                 "--allow-draft")
        self.assertEqual(code, 0, err)
        json.loads(out)
        self.assertIn("draft", err.lower())


class TestStdoutIsRealUtf8(unittest.TestCase):
    """The in-process tests above redirect stdout to a StringIO, which is text and
    therefore cannot see an encoding bug. A real process can: on Windows stdout
    encodes with the console codepage, so a template carrying anything outside ASCII
    was written as cp1252 and the redirected file was not valid UTF-8 at all.
    """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.wd = os.path.join(self.tmp, "work")
        self.cli_run(["init", "--from", BASE_TEMPLATE, "--workdir", self.wd,
                      "--profile", PROFILE_FIXTURE])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli_run(self, args):
        env = dict(os.environ)
        env["PYTHONPATH"] = SCRIPTS + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run([sys.executable, ENTRY] + args, cwd=self.tmp, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return proc

    def test_the_stream_is_utf8_whatever_the_console_codepage_is(self):
        proc = self.cli_run(["export", "--workdir", self.wd, "--out", "-"])
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        envelope = json.loads(proc.stdout.decode("utf-8"))  # raises on a bad encoding
        self.assertEqual(list(envelope.keys()), ELEMENTOR_ENVELOPE_KEYS)

    def test_the_stream_is_byte_identical_to_the_file_export(self):
        path = os.path.join(self.tmp, "on-disk.json")
        self.cli_run(["export", "--workdir", self.wd, "--out", path])
        proc = self.cli_run(["export", "--workdir", self.wd, "--out", "-"])
        with open(path, "rb") as fh:
            self.assertEqual(fh.read(), proc.stdout)


class TestDefaultWorkdir(DeliveryCase):
    def test_init_without_workdir_uses_the_default_and_says_where(self):
        code, out, err = run_cli("init", "--from", BASE_TEMPLATE,
                                 "--profile", PROFILE_FIXTURE)
        self.assertEqual(code, 0, out + err)
        default = cli.default_workdir()
        self.assertTrue(os.path.isfile(os.path.join(default, "document.json")))
        self.assertIn(default, out + err)

    def test_later_commands_find_the_same_default_workspace(self):
        run_cli("init", "--from", BASE_TEMPLATE, "--profile", PROFILE_FIXTURE)
        code, out, err = run_cli("inspect", "--widgets")
        self.assertEqual(code, 0, out + err)
        self.assertIn("crecs_property_data", out)

    def test_the_default_is_announced_on_stderr_not_stdout(self):
        # `inspect --json` must stay machine-readable even when the default is in use.
        run_cli("init", "--from", BASE_TEMPLATE, "--profile", PROFILE_FIXTURE)
        _, out, err = run_cli("inspect", "--widgets", "--json")
        json.loads(out)
        self.assertIn(cli.default_workdir(), err)

    def test_the_environment_variable_moves_the_default(self):
        moved = os.path.join(self.tmp, "somewhere-else")
        os.environ[cli.WORKDIR_ENV] = moved
        self.assertEqual(cli.default_workdir(), moved)
        code, out, err = run_cli("init", "--from", BASE_TEMPLATE,
                                 "--profile", PROFILE_FIXTURE)
        self.assertEqual(code, 0, out + err)
        self.assertTrue(os.path.isfile(os.path.join(moved, "document.json")))

    def test_an_explicit_workdir_still_wins(self):
        code, _, err = run_cli("inspect", "--workdir", self.wd, "--widgets")
        self.assertEqual(code, 0, err)
        # The default was never created by this call.
        self.assertFalse(os.path.isdir(cli.default_workdir()))

    def test_no_workspace_anywhere_names_the_default_path(self):
        code, out, err = run_cli("inspect", "--widgets")
        self.assertNotEqual(code, 0)
        self.assertIn(cli.default_workdir(), out + err)
        self.assertIn("init", (out + err).lower())

    def test_the_whole_cycle_runs_without_naming_a_directory(self):
        # The requirement in one test: no --workdir, no --out path, a file on stdout.
        code, _, err = run_cli("init", "--from", BASE_TEMPLATE,
                               "--profile", PROFILE_FIXTURE)
        self.assertEqual(code, 0, err)
        code, out, err = run_cli("export", "--out", "-")
        self.assertEqual(code, 0, err)
        envelope = json.loads(out)
        self.assertEqual(list(envelope.keys()), ELEMENTOR_ENVELOPE_KEYS)
        self.assertTrue(envelope["content"])


class TestSkillSaysToDeliver(unittest.TestCase):
    """The instruction has to exist where the assistant actually reads it."""

    def setUp(self):
        with open(SKILL_MD, encoding="utf-8") as fh:
            self.text = fh.read()

    def test_skill_md_tells_the_assistant_to_hand_over_the_file(self):
        lowered = self.text.lower()
        self.assertTrue(
            any(word in lowered for word in ("hand it to", "give them the file",
                                             "deliver")),
            "SKILL.md never says to give the person the exported file",
        )

    def test_skill_md_documents_the_stdout_escape_hatch(self):
        self.assertIn("--out -", self.text)

    def test_skill_md_says_how_to_import_it(self):
        lowered = self.text.lower()
        self.assertIn("saved templates", lowered)
        self.assertIn("crecs_custom_property_page_template_shortcode", self.text)

    def test_the_delivery_step_is_part_of_the_loop(self):
        # The loop line at the top is what gets followed; a step documented only in a
        # later paragraph is a step that gets skipped.
        loop = [line for line in self.text.splitlines() if "validate" in line
                and "export" in line and "->" in line]
        self.assertTrue(loop, "the loop line is gone")
        self.assertTrue(any("deliver" in line.lower() for line in loop),
                        "deliver is not in the loop: " + " | ".join(loop))


if __name__ == "__main__":
    unittest.main()
