"""`crecs_preview.py connect`: the assistant saves the preview's session file itself.

The person using the skill is not technical. The Template preview screen shows the
session file in a box; reading that box and saving it is the assistant's job, not
theirs, and it has to work the first time without anyone editing JSON by hand. These
run `connect` against a real local server, as test_transport_errors does, so the check
with the site is exercised end to end.
"""

import contextlib
import io
import json
import os
import shutil
import socket
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import crecs_preview

TOKEN = "tok-secret-4f9a2b"


class Handler(BaseHTTPRequestHandler):
    """Answers the state request; `refuse` makes it answer as a stale token gets answered."""

    refuse = False
    seen = []

    def do_GET(self):
        Handler.seen.append((self.path, self.headers.get("Authorization")))
        if Handler.refuse:
            body, status = {"code": "crecs_preview_unauthorised",
                            "message": "Unknown session or wrong token.", "data": {"status": 401}}, 401
        else:
            body, status = {"head": 0, "last_state": "ready"}, 200
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):  # keep the test output readable
        pass


class Connect(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        Handler.refuse = False
        Handler.seen = []
        self.dir = tempfile.mkdtemp(prefix="crecs-connect-test-")
        self.sessions = os.path.join(self.dir, "sessions")
        # One file per kind of preview: the search page's carries its kind in its name, and
        # the property page's keeps the name it has always had.
        self.saved = os.path.join(self.sessions, "preview-127.0.0.1-search.json")
        self.saved_property = os.path.join(self.sessions, "preview-127.0.0.1.json")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def box(self, token=TOKEN, kind="search", base=None):
        """The box's text, as the Template preview screen prints it."""
        data = {"base": base or self.base, "id": "ps_test1", "token": token}
        if kind:
            data["kind"] = kind
        return json.dumps(data, indent=4)

    def run_connect(self, text=None, *extra):
        out, err = io.StringIO(), io.StringIO()
        stdin = io.StringIO(text if text is not None else "")
        real_stdin = crecs_preview.sys.stdin
        crecs_preview.sys.stdin = stdin
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = crecs_preview.main(["connect", "--session-dir", self.sessions] + list(extra))
        finally:
            crecs_preview.sys.stdin = real_stdin
        return code, out.getvalue(), err.getvalue()

    def stored(self, path=None):
        with open(path or self.saved, encoding="utf-8") as fh:
            return json.load(fh)

    # -- the ordinary path ---------------------------------------------------------

    def test_the_box_is_checked_with_the_site_and_saved(self):
        code, out, err = self.run_connect(self.box())
        self.assertEqual(0, code, err)
        self.assertEqual({"base": self.base, "id": "ps_test1", "token": TOKEN, "kind": "search"},
                         self.stored())
        self.assertEqual([("/wp-json/crecs/preview/v1/sessions/ps_test1/state", "Bearer " + TOKEN)],
                         Handler.seen)
        self.assertIn("search page", out)
        self.assertIn(self.saved, out)
        self.assertNotIn(TOKEN, out + err, "connect printed the token")

    def test_text_around_the_box_is_ignored(self):
        pasted = "~/.crecs/preview-127.0.0.1.json\n" + self.box(kind=None) + "\n\nOpen the preview\n"
        code, out, _err = self.run_connect(pasted)
        self.assertEqual(0, code)
        self.assertNotIn("kind", self.stored(self.saved_property))
        self.assertIn("property page", out)

    def test_the_saved_file_is_what_the_other_commands_read(self):
        self.run_connect(self.box())
        base, sid, token = crecs_preview.load_session(crecs_preview.Path(self.saved), None)
        self.assertEqual((self.base, "ps_test1", TOKEN), (base, sid, token))

    def test_a_new_link_replaces_the_old_token(self):
        self.run_connect(self.box())
        code, _out, _err = self.run_connect(self.box(token="tok-after-new-link"))
        self.assertEqual(0, code)
        self.assertEqual("tok-after-new-link", self.stored()["token"])

    def test_from_a_file(self):
        path = os.path.join(self.dir, "box.txt")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.box())
        code, _out, err = self.run_connect(None, "--from", path)
        self.assertEqual(0, code, err)
        self.assertEqual(TOKEN, self.stored()["token"])

    # -- what is refused, and what is left alone -----------------------------------

    def test_a_session_the_site_refuses_is_not_saved_over_a_working_one(self):
        self.run_connect(self.box())
        Handler.refuse = True
        code, out, err = self.run_connect(self.box(token="tok-stale"))
        self.assertEqual(2, code)
        self.assertEqual(TOKEN, self.stored()["token"], "a refused session replaced the working one")
        self.assertIn("New link", err, "the refusal does not say how to get a working session")
        self.assertNotIn("tok-stale", out + err)

    def test_text_that_is_not_a_session_is_refused_plainly(self):
        for text in ("", "hello", "{not json}", json.dumps({"base": self.base, "id": "ps_x"}),
                     json.dumps({"base": "ftp://x", "id": "ps_x", "token": "t"}),
                     json.dumps({"base": self.base, "id": "ps_x", "token": "t", "kind": "blog"})):
            with self.subTest(text=text):
                code, _out, err = self.run_connect(text)
                self.assertEqual(3, code)
                self.assertTrue(err.startswith("refused:"), err)
                self.assertNotIn("Traceback", err)
        self.assertFalse(os.path.exists(self.saved))

    def test_an_unreachable_site_still_saves_and_says_so(self):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            closed = "http://127.0.0.1:%d" % probe.getsockname()[1]
        code, _out, err = self.run_connect(self.box(base=closed))
        self.assertEqual(3, code)
        self.assertIn("could not be reached", err)
        self.assertTrue(os.path.exists(self.saved))


if __name__ == "__main__":
    unittest.main()
