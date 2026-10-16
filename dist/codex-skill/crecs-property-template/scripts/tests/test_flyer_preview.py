"""The flyer preview, as `crecs_preview.py` speaks it (skill 1.4.0).

A flyer session is a preview like the search page's, with two differences the transport has
to know about: it is its own kind, so a site now has up to three sessions at once (a property
template, the search page, a flyer) and each needs its own file; and it can ask the site for
the exact PDF CRE Cloud's printer makes, with a picture of every page, which the assistant
opens and looks at.

These run the real commands against a real local server, as test_connect does, so the HTTP
is exercised end to end. The server is a small fake of the plugin's preview module: it
answers what the tests queue for each route, and records what it was asked.

The person never sees any of this: nothing printed here may carry a session token, and what
is printed is plain words, because the assistant repeats it to someone who owns a property
website.
"""

import base64
import contextlib
import io
import json
import os
import shutil
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

import crecs_preview
from crecs_preview import canonical_hash

API = "/wp-json/crecs/preview/v1"

TOKEN_PROPERTY = "tok-property-59f0d2"
TOKEN_SEARCH = "tok-search-3b8a41"
TOKEN_FLYER = "tok-flyer-7c1d9e"
ALL_TOKENS = (TOKEN_PROPERTY, TOKEN_SEARCH, TOKEN_FLYER)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"\x01" * 20
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

DOCUMENT = {
    "type": "crecs-flyer-layout", "version": 1, "title": "Test flyer",
    "content": [{"id": "abcd1234", "elType": "container", "widgetType": "crecs_flyer",
                 "settings": {"orientation": "portrait"}, "elements": []}],
}


def b64(data):
    return base64.b64encode(data).decode("ascii")


class Site:
    """A fake preview module on a local port.

    `on(method, path, status, payload, headers)` queues one answer for a route; a route's
    last answer repeats. `requests` records what arrived: method, path (below the REST
    namespace), query, the Authorization header and the JSON body.
    """

    def __init__(self):
        self.routes = {}
        self.requests = []
        site = self

        class Handler(BaseHTTPRequestHandler):
            def _serve(self):
                parts = urllib.parse.urlsplit(self.path)
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                path = parts.path[len(API):] if parts.path.startswith(API) else parts.path
                site.requests.append({
                    "method": self.command, "path": path,
                    "query": dict(urllib.parse.parse_qsl(parts.query)),
                    "auth": self.headers.get("Authorization"),
                    "body": json.loads(raw) if raw else None,
                })
                queue = site.routes.get((self.command, path))
                if not queue:
                    status, payload, headers = 404, {"code": "rest_no_route", "message": "No route."}, {}
                else:
                    status, payload, headers = queue.pop(0) if len(queue) > 1 else queue[0]
                blob = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(blob)))
                for name, value in (headers or {}).items():
                    self.send_header(name, value)
                self.end_headers()
                self.wfile.write(blob)

            do_GET = do_POST = do_PUT = do_DELETE = _serve

            def log_message(self, *args):  # keep the test output readable
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.base = "http://127.0.0.1:%d" % self.server.server_port
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True).start()

    def on(self, method, path, status, payload, headers=None):
        self.routes.setdefault((method, path), []).append((status, payload, headers))

    def stop(self):
        self.server.shutdown()
        self.server.server_close()

    def asked(self, method, path):
        return [r for r in self.requests if r["method"] == method and r["path"] == path]


def box(base, session_id, token, kind=None):
    """The text the Template preview screen shows in its box."""
    data = {"base": base, "id": session_id, "token": token}
    if kind:
        data["kind"] = kind
    return json.dumps(data, indent=4)


class Base(unittest.TestCase):
    """A site, a folder of saved sessions, and a way to run the command line."""

    def setUp(self):
        self.site = Site()
        self.dir = tempfile.mkdtemp(prefix="crecs-flyer-preview-test-")
        self.sessions = Path(self.dir) / "sessions"
        self.sessions.mkdir()
        patcher = mock.patch.object(crecs_preview, "DEFAULT_SESSION_DIR", self.sessions)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sleeps = []
        waiter = mock.patch.object(crecs_preview, "pause", lambda seconds: self.sleeps.append(seconds))
        waiter.start()
        self.addCleanup(waiter.stop)

    def tearDown(self):
        self.site.stop()
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_cli(self, argv, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        real_stdin = crecs_preview.sys.stdin
        if stdin is not None:
            crecs_preview.sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = crecs_preview.main(list(argv))
        finally:
            crecs_preview.sys.stdin = real_stdin
        return code, out.getvalue(), err.getvalue()

    def save_session(self, name, session_id, token, kind=None):
        data = {"base": self.site.base, "id": session_id, "token": token}
        if kind:
            data["kind"] = kind
        path = self.sessions / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def no_token(self, *texts):
        joined = "\n".join(texts)
        for token in ALL_TOKENS:
            self.assertNotIn(token, joined, "a session token was printed")


# ---------------------------------------------------------------------------------------
# one session file per kind
# ---------------------------------------------------------------------------------------


class SessionFilePerKind(Base):

    def state_route(self, session_id):
        self.site.on("GET", "/sessions/%s/state" % session_id, 200, {"head": 0, "last_state": "ready"})

    def connect(self, session_id, token, kind=None, *extra):
        self.state_route(session_id)
        return self.run_cli(["connect", "--session-dir", str(self.sessions)] + list(extra),
                            stdin=box(self.site.base, session_id, token, kind))

    def test_a_flyer_box_is_accepted_and_keeps_its_kind(self):
        session = crecs_preview.parse_session_text(box(self.site.base, "ps_flyer", TOKEN_FLYER, "flyer"))
        self.assertEqual("flyer", session["kind"])
        self.assertEqual("ps_flyer", session["id"])

    def test_a_property_box_still_has_no_kind(self):
        session = crecs_preview.parse_session_text(box(self.site.base, "ps_prop", TOKEN_PROPERTY))
        self.assertNotIn("kind", session)

    def test_an_unknown_kind_is_still_refused(self):
        with self.assertRaises(crecs_preview.SessionText):
            crecs_preview.parse_session_text(box(self.site.base, "ps_x", "tok", "blog"))

    def test_a_flyer_session_is_saved_under_its_kind(self):
        code, out, err = self.connect("ps_flyer", TOKEN_FLYER, "flyer")
        self.assertEqual(0, code, err)
        saved = self.sessions / "preview-127.0.0.1-flyer.json"
        self.assertTrue(saved.is_file())
        self.assertEqual({"base": self.site.base, "id": "ps_flyer", "token": TOKEN_FLYER, "kind": "flyer"},
                         json.loads(saved.read_text(encoding="utf-8")))
        self.assertIn("flyer", out)
        self.assertIn(str(saved), out)
        self.no_token(out, err)

    def test_a_search_session_is_saved_under_its_kind(self):
        code, out, err = self.connect("ps_search", TOKEN_SEARCH, "search")
        self.assertEqual(0, code, err)
        self.assertTrue((self.sessions / "preview-127.0.0.1-search.json").is_file())
        self.assertFalse((self.sessions / "preview-127.0.0.1.json").exists())

    def test_a_property_session_keeps_the_name_it_always_had(self):
        code, _out, err = self.connect("ps_prop", TOKEN_PROPERTY)
        self.assertEqual(0, code, err)
        saved = self.sessions / "preview-127.0.0.1.json"
        self.assertTrue(saved.is_file())
        self.assertNotIn("kind", json.loads(saved.read_text(encoding="utf-8")))

    def test_the_three_sessions_of_one_site_live_side_by_side(self):
        for sid, token, kind in (("ps_prop", TOKEN_PROPERTY, None), ("ps_search", TOKEN_SEARCH, "search"),
                                 ("ps_flyer", TOKEN_FLYER, "flyer")):
            self.assertEqual(0, self.connect(sid, token, kind)[0])
        names = sorted(p.name for p in self.sessions.iterdir())
        self.assertEqual(["preview-127.0.0.1-flyer.json", "preview-127.0.0.1-search.json",
                          "preview-127.0.0.1.json"], names)

    def test_a_new_link_replaces_only_its_own_kinds_file(self):
        self.connect("ps_search", TOKEN_SEARCH, "search")
        self.connect("ps_flyer", TOKEN_FLYER, "flyer")
        self.connect("ps_flyer", "tok-flyer-after-new-link", "flyer")
        flyer = json.loads((self.sessions / "preview-127.0.0.1-flyer.json").read_text(encoding="utf-8"))
        search = json.loads((self.sessions / "preview-127.0.0.1-search.json").read_text(encoding="utf-8"))
        self.assertEqual("tok-flyer-after-new-link", flyer["token"])
        self.assertEqual(TOKEN_SEARCH, search["token"])

    def test_a_box_of_another_kind_than_asked_for_is_refused(self):
        code, _out, err = self.connect("ps_search", TOKEN_SEARCH, "search", "--kind", "flyer")
        self.assertEqual(3, code)
        self.assertIn("search page", err)
        self.assertIn("flyer", err)
        self.assertEqual([], list(self.sessions.iterdir()))

    # -- an old search file keeps working, and is not lost -----------------------------

    def old_search_file(self):
        return self.save_session("preview-127.0.0.1.json", "ps_search", TOKEN_SEARCH, "search")

    def test_connecting_a_flyer_moves_an_old_search_file_to_its_new_name(self):
        old = self.old_search_file()
        self.assertEqual(0, self.connect("ps_flyer", TOKEN_FLYER, "flyer")[0])
        self.assertFalse(old.exists(), "the old search file is still under the property's name")
        moved = self.sessions / "preview-127.0.0.1-search.json"
        self.assertEqual(TOKEN_SEARCH, json.loads(moved.read_text(encoding="utf-8"))["token"])
        self.assertTrue((self.sessions / "preview-127.0.0.1-flyer.json").is_file())

    def test_connecting_a_property_does_not_overwrite_an_old_search_session(self):
        self.old_search_file()
        self.assertEqual(0, self.connect("ps_prop", TOKEN_PROPERTY)[0])
        search = json.loads((self.sessions / "preview-127.0.0.1-search.json").read_text(encoding="utf-8"))
        self.assertEqual("ps_search", search["id"])
        prop = json.loads((self.sessions / "preview-127.0.0.1.json").read_text(encoding="utf-8"))
        self.assertEqual("ps_prop", prop["id"])

    def test_an_old_file_that_holds_a_property_session_is_left_alone(self):
        old = self.save_session("preview-127.0.0.1.json", "ps_prop", TOKEN_PROPERTY)
        self.connect("ps_flyer", TOKEN_FLYER, "flyer")
        self.assertTrue(old.is_file())
        self.assertFalse((self.sessions / "preview-127.0.0.1-search.json").exists())

    def test_a_newer_search_file_is_never_replaced_by_the_old_one(self):
        self.old_search_file()
        self.save_session("preview-127.0.0.1-search.json", "ps_search_new", "tok-search-new", "search")
        self.connect("ps_flyer", TOKEN_FLYER, "flyer")
        kept = json.loads((self.sessions / "preview-127.0.0.1-search.json").read_text(encoding="utf-8"))
        self.assertEqual("ps_search_new", kept["id"])

    def test_the_old_search_file_still_serves_a_search_command(self):
        self.old_search_file()
        self.site.on("GET", "/sessions/ps_search/search-options", 200,
                     {"property_types": ["Office"], "brokers": ["Jane Doe"]})
        code, out, err = self.run_cli(["options"])
        self.assertEqual(0, code, err)
        self.assertIn("Office", out)
        self.assertEqual("Bearer " + TOKEN_SEARCH, self.site.requests[-1]["auth"])

    def test_the_old_search_file_serves_state_with_kind_search(self):
        self.old_search_file()
        self.state_route("ps_search")
        code, _out, err = self.run_cli(["state", "--kind", "search"])
        self.assertEqual(0, code, err)
        self.assertEqual("/sessions/ps_search/state", self.site.requests[-1]["path"])


# ---------------------------------------------------------------------------------------
# which session a command uses
# ---------------------------------------------------------------------------------------


class WhichSession(Base):

    def setUp(self):
        super().setUp()
        self.prop = self.save_session("preview-127.0.0.1.json", "ps_prop", TOKEN_PROPERTY)
        self.search = self.save_session("preview-127.0.0.1-search.json", "ps_search", TOKEN_SEARCH, "search")
        self.flyer = self.save_session("preview-127.0.0.1-flyer.json", "ps_flyer", TOKEN_FLYER, "flyer")
        for sid in ("ps_prop", "ps_search", "ps_flyer"):
            self.site.on("GET", "/sessions/%s/state" % sid, 200, {"head": 1, "ready_revision": 1})
        self.site.on("GET", "/sessions/ps_search/search-options", 200, {"property_types": [], "brokers": []})
        self.site.on("POST", "/sessions/ps_flyer/flyer-pdf", 404, {"code": "crecs_preview_no_revision",
                                                                    "message": "This preview has no ready revision."})

    def last_session(self):
        return self.site.requests[-1]["path"].split("/")[2]

    def test_an_explicit_session_file_wins_whatever_its_kind(self):
        code, _out, err = self.run_cli(["state", "--session-file", str(self.search), "--kind", "flyer"])
        # The file is the person's choice; naming a kind it is not is the one thing refused.
        self.assertEqual(3, code)
        self.assertIn("search page", err)
        code, _out, err = self.run_cli(["state", "--session-file", str(self.search)])
        self.assertEqual(0, code, err)
        self.assertEqual("ps_search", self.last_session())

    def test_a_flyer_command_uses_the_flyer_session_and_says_which(self):
        code, out, err = self.run_cli(["pdf"])
        self.assertEqual("ps_flyer", self.last_session())
        self.assertIn("flyer", err.lower())
        self.assertIn("127.0.0.1", err)
        self.no_token(out, err)

    def test_a_search_command_uses_the_search_session(self):
        code, _out, err = self.run_cli(["options"])
        self.assertEqual(0, code, err)
        self.assertEqual("ps_search", self.last_session())

    def test_kind_picks_the_session_for_a_command_that_has_no_kind_of_its_own(self):
        for kind, expected in (("flyer", "ps_flyer"), ("search", "ps_search"), ("property", "ps_prop")):
            with self.subTest(kind=kind):
                code, _out, err = self.run_cli(["state", "--kind", kind])
                self.assertEqual(0, code, err)
                self.assertEqual(expected, self.last_session())

    def test_kind_may_come_before_the_command(self):
        code, _out, err = self.run_cli(["--kind", "flyer", "state"])
        self.assertEqual(0, code, err)
        self.assertEqual("ps_flyer", self.last_session())

    def test_with_several_sessions_and_no_kind_it_asks_rather_than_guesses(self):
        before = len(self.site.requests)
        code, out, err = self.run_cli(["state"])
        self.assertEqual(3, code)
        self.assertEqual(before, len(self.site.requests), "it asked the site with a guessed session")
        for word in ("flyer", "search", "property", "--kind"):
            self.assertIn(word, err)
        self.no_token(out, err)

    def test_with_exactly_one_session_it_uses_it_and_says_so(self):
        self.prop.unlink()
        self.search.unlink()
        code, _out, err = self.run_cli(["state"])
        self.assertEqual(0, code, err)
        self.assertEqual("ps_flyer", self.last_session())
        self.assertIn("flyer", err.lower())

    def test_a_flyer_command_with_no_flyer_session_says_how_to_start_one(self):
        self.flyer.unlink()
        before = len(self.site.requests)
        code, _out, err = self.run_cli(["pdf"])
        self.assertEqual(3, code)
        self.assertEqual(before, len(self.site.requests))
        self.assertIn("Start flyer preview", err)
        self.assertIn("connect", err)

    def test_the_session_is_found_by_the_site_when_base_is_given(self):
        # A second site's flyer session sits in the same folder: --base says which site.
        (self.sessions / "preview-other.test-flyer.json").write_text(json.dumps(
            {"base": "http://other.test", "id": "ps_other", "token": "tok-other-0000", "kind": "flyer"}),
            encoding="utf-8")
        code, _out, err = self.run_cli(["state", "--kind", "flyer", "--base", self.site.base])
        self.assertEqual(0, code, err)
        self.assertEqual("ps_flyer", self.last_session())

    def test_two_sites_and_no_base_is_a_question_not_a_guess(self):
        (self.sessions / "preview-other.test-flyer.json").write_text(json.dumps(
            {"base": "http://other.test", "id": "ps_other", "token": "tok-other-0000", "kind": "flyer"}),
            encoding="utf-8")
        before = len(self.site.requests)
        code, _out, err = self.run_cli(["state", "--kind", "flyer"])
        self.assertEqual(3, code)
        self.assertEqual(before, len(self.site.requests))
        self.assertIn("--base", err)
        self.assertNotIn("tok-other-0000", err)

    def test_when_both_names_hold_a_search_session_the_new_name_wins(self):
        self.save_session("preview-127.0.0.1.json", "ps_search_old", "tok-search-old", "search")
        code, _out, err = self.run_cli(["state", "--kind", "search"])
        self.assertEqual(0, code, err)
        self.assertEqual("ps_search", self.last_session())

    def test_nothing_saved_and_no_kind_is_the_old_message(self):
        for path in self.sessions.iterdir():
            path.unlink()
        code, _out, err = self.run_cli(["state", "--base", self.site.base])
        self.assertEqual(3, code)
        self.assertIn("session", err)


# ---------------------------------------------------------------------------------------
# the flyer's own words
# ---------------------------------------------------------------------------------------


class FlyerCommands(Base):

    def setUp(self):
        super().setUp()
        self.file = self.save_session("flyer.json", "ps_flyer", TOKEN_FLYER, "flyer")

    def run_flyer(self, *argv):
        return self.run_cli(list(argv) + ["--session-file", str(self.file)])

    def test_apply_hashes_the_content_as_a_search_layout_is_hashed(self):
        content = DOCUMENT["content"]
        self.site.on("GET", "/sessions/ps_flyer/state", 200, {"kind": "flyer", "head": 3})
        self.site.on("POST", "/sessions/ps_flyer/revision", 200,
                     {"revision": 4, "state": "ready", "hash": canonical_hash(content)})
        doc = Path(self.dir) / "flyer-layout.json"
        doc.write_text(json.dumps(DOCUMENT), encoding="utf-8")
        code, out, err = self.run_flyer("apply", "--document", str(doc), "--key", "k1")
        self.assertEqual(0, code, err)
        sent = self.site.asked("POST", "/sessions/ps_flyer/revision")[0]["body"]
        self.assertEqual(3, sent["base_revision"])
        self.assertEqual(content, sent["document"])
        self.assertEqual("k1", sent["idempotency_key"])
        self.assertNotIn("differs", err, "the server's hash and the local one disagreed")
        self.assertIn("4", out)

    def test_apply_warns_when_the_servers_hash_is_not_the_local_one(self):
        self.site.on("GET", "/sessions/ps_flyer/state", 200, {"kind": "flyer", "head": 0})
        self.site.on("POST", "/sessions/ps_flyer/revision", 200,
                     {"revision": 1, "state": "ready", "hash": "f" * 64})
        doc = Path(self.dir) / "flyer-layout.json"
        doc.write_text(json.dumps(DOCUMENT), encoding="utf-8")
        _code, _out, err = self.run_flyer("apply", "--document", str(doc))
        self.assertIn("differs", err)

    def test_a_refused_flyer_names_the_block_at_fault(self):
        self.site.on("GET", "/sessions/ps_flyer/state", 200, {"kind": "flyer", "head": 0})
        self.site.on("POST", "/sessions/ps_flyer/revision", 422, {
            "code": "crecs_preview_invalid", "message": "The document did not pass server-side validation.",
            "findings": [{"level": "error", "code": "E-FL-FONT", "node": "fl1a0022", "element": "fl1a0022",
                          "message": "Arial is not a font the flyer printer has."}], "head": 0})
        doc = Path(self.dir) / "flyer-layout.json"
        doc.write_text(json.dumps(DOCUMENT), encoding="utf-8")
        code, _out, err = self.run_flyer("apply", "--document", str(doc))
        self.assertEqual(2, code)
        self.assertIn("E-FL-FONT", err)
        self.assertIn("fl1a0022", err)

    def flyer_state(self, **extra):
        state = {"kind": "flyer", "head": 3, "ready_revision": 3, "ready_hash": "ab" * 32,
                 "last_state": "ready", "last_revision": 3, "failures": [],
                 "property": "hwy-380-farmersville", "expires_at": "2026-10-14 10:00:00"}
        state.update(extra)
        self.site.on("GET", "/sessions/ps_flyer/state", 200, state)

    def test_state_says_it_in_plain_words(self):
        self.flyer_state(last_state="rejected", last_revision=4,
                         failures=[{"revision": 4, "state": "rejected", "class": "validation"},
                                   {"revision": 2, "state": "render_failed", "class": "render"}])
        code, out, err = self.run_flyer("state")
        self.assertEqual(0, code, err)
        self.assertIn("flyer", out.lower())
        self.assertIn("hwy-380-farmersville", out)
        self.assertIn("revision 3", out)
        self.assertIn("revision 4", out)
        self.assertIn("refused", out)
        self.assertIn("2026-10-14", out)
        # No raw key and value dump, no class names, no token.
        self.assertNotIn("failure_class", out)
        self.assertNotIn("validation", out)
        self.assertNotIn("{", out)
        self.no_token(out, err)

    def test_a_ready_flyer_with_no_failures_says_so(self):
        self.flyer_state()
        _code, out, _err = self.run_flyer("state")
        self.assertIn("ready", out)
        self.assertNotIn("refused", out)

    def test_a_flyer_with_no_property_says_so(self):
        self.flyer_state(property="")
        _code, out, _err = self.run_flyer("state")
        self.assertIn("no property", out)

    def test_state_json_is_the_servers_answer(self):
        self.flyer_state()
        code, out, _err = self.run_flyer("state", "--json")
        self.assertEqual(0, code)
        data = json.loads(out)
        self.assertEqual("flyer", data["kind"])
        self.assertEqual("hwy-380-farmersville", data["property"])

    def test_other_kinds_print_state_as_they_always_did(self):
        self.site.on("GET", "/sessions/ps_search/state", 200, {"kind": "search", "head": 2, "ready_revision": 2,
                                                              "ready_hash": "a" * 64, "last_state": "ready",
                                                              "property": "", "live_hash": "a" * 64})
        search = self.save_session("search.json", "ps_search", TOKEN_SEARCH, "search")
        code, out, _err = self.run_cli(["state", "--session-file", str(search)])
        self.assertEqual(0, code)
        self.assertIn("\nlive                   yes\n", "\n" + out)
        self.assertIn("head                   2", out)

    def test_current_describes_the_design_and_saves_it(self):
        document = json.loads(json.dumps(DOCUMENT))
        document["content"][0]["elements"] = [
            {"id": "page0001", "elType": "container", "widgetType": "crecs_flyer_page", "settings": {}, "elements": []},
            {"id": "page0002", "elType": "container", "widgetType": "crecs_flyer_page", "settings": {}, "elements": []},
        ]
        self.site.on("GET", "/sessions/ps_flyer/revision", 200, {
            "document": document, "manifest": {"revision": 5, "kind": "flyer", "property_previewed": "hwy-380-farmersville"}})
        out_file = Path(self.dir) / "flyer.json"
        code, out, err = self.run_flyer("current", "--out", str(out_file))
        self.assertEqual(0, code, err)
        self.assertEqual(document, json.loads(out_file.read_text(encoding="utf-8")))
        self.assertIn("Test flyer", out)
        self.assertIn("revision 5", out)
        self.assertIn("portrait", out)
        self.assertIn("2 designed pages", out)
        self.assertNotIn("manifest", out)

    def test_capabilities_says_whether_the_exact_pdf_can_be_made(self):
        caps = {"product": "crecs-preview", "contract": 1, "session_kinds": ["property", "search", "flyer"],
                "flyer_layout": {"type": "crecs-flyer-layout", "version": 1},
                "operations": ["flyer.pdf.make", "flyer.pdf.get"], "flyer_pdf": {"available": True}}
        self.site.on("GET", "/capabilities", 200, caps)
        code, out, err = self.run_cli(["capabilities", "--base", self.site.base])
        self.assertEqual(0, code, err)
        self.assertIn("flyer_pdf", out)
        self.assertIn("available", out)
        self.assertNotIn("not available", out)
        self.assertIn("flyer", out)

    def test_capabilities_gives_the_reason_when_it_cannot(self):
        caps = {"product": "crecs-preview", "contract": 1, "session_kinds": ["property", "search", "flyer"],
                "flyer_pdf": {"available": False, "reason": "This site is not connected to CRE Cloud."}}
        self.site.on("GET", "/capabilities", 200, caps)
        _code, out, _err = self.run_cli(["capabilities", "--base", self.site.base])
        self.assertIn("not available", out)
        self.assertIn("This site is not connected to CRE Cloud.", out)

    def test_capabilities_of_an_older_plugin_says_nothing_about_the_pdf(self):
        self.site.on("GET", "/capabilities", 200, {"product": "crecs-preview", "contract": 1})
        code, out, _err = self.run_cli(["capabilities", "--base", self.site.base])
        self.assertEqual(0, code)
        self.assertNotIn("flyer_pdf", out)


# ---------------------------------------------------------------------------------------
# the exact PDF
# ---------------------------------------------------------------------------------------


def made(revision=4, dpi=96, pages=None, warnings=None, cached=False, **extra):
    pages = pages if pages is not None else [
        {"n": 1, "source": "design"}, {"n": 2, "source": "design"},
        {"n": 3, "source": "attachment", "attachment_id": 3656, "attachment_name": "Available Space",
         "layout": "8.5x11 - Inside Layout Landscape", "global": False},
        {"n": 4, "source": "attachment", "attachment_id": 223, "attachment_name": "IABS",
         "layout": "8.5x11", "global": True},
    ]
    data = {
        "revision": revision, "dpi": dpi, "property": "hwy-380-farmersville", "page_count": len(pages),
        "pdf_bytes": 412345, "pages": pages,
        "images": [{"n": p["n"], "width": 1056, "height": 816, "bytes": len(PNG)} for p in pages],
        "warnings": warnings or [], "timings_ms": {"total": 3112},
        "created_at": "2026-10-13 15:04:05", "cached": cached,
    }
    data.update(extra)
    return data


def fetched(meta, png=PNG, pdf=None, only=None):
    data = json.loads(json.dumps(meta))
    for image in data["images"]:
        if only is None or image["n"] in only:
            image["png"] = b64(png if not callable(png) else png(image["n"]))
        else:
            image["png"] = None
    if pdf is not None:
        data["pdf"] = b64(pdf)
    return data


class Pdf(Base):

    PATH = "/sessions/ps_flyer/flyer-pdf"

    def setUp(self):
        super().setUp()
        self.file = self.save_session("flyer.json", "ps_flyer", TOKEN_FLYER, "flyer")
        self.out = Path(self.dir) / "pages"

    def run_pdf(self, *argv):
        code, out, err = self.run_cli(["pdf", "--session-file", str(self.file)] + list(argv))
        self.no_token(out, err)
        return code, out, err

    def serve(self, meta=None, png=PNG, pdf=None):
        meta = meta or made()
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta, png=png, pdf=pdf))
        return meta

    def names(self, folder=None):
        return sorted(p.name for p in (folder or self.out).iterdir())

    # -- the ordinary path -------------------------------------------------------------

    def test_it_makes_the_pdf_then_saves_every_page_as_a_picture(self):
        self.serve()
        code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual(["page-1.png", "page-2.png", "page-3.png", "page-4.png"], self.names())
        for page in range(1, 5):
            self.assertEqual(PNG, (self.out / ("page-%d.png" % page)).read_bytes())
        make = self.site.asked("POST", self.PATH)[0]
        self.assertEqual({"dpi": 96}, make["body"])
        self.assertEqual("Bearer " + TOKEN_FLYER, make["auth"])
        get = self.site.asked("GET", self.PATH)[0]
        self.assertEqual({"revision": "4", "include": "images"}, get["query"])

    def test_the_summary_says_what_every_page_is(self):
        self.serve()
        _code, out, _err = self.run_pdf("--out-dir", str(self.out))
        self.assertIn("revision 4", out)
        self.assertIn("4 pages", out)
        self.assertIn("page 1", out)
        self.assertIn("designed page", out)
        self.assertIn('"Available Space"', out)
        self.assertIn("header and footer", out)
        self.assertIn('"IABS"', out)
        self.assertIn("company", out)
        self.assertIn(str(self.out / "page-1.png"), out)
        self.assertIn("96 dpi", out)

    def test_without_warnings_it_says_there_are_none(self):
        self.serve()
        _code, out, _err = self.run_pdf("--out-dir", str(self.out))
        self.assertIn("no warnings", out.lower())

    def test_the_whole_pdf_comes_only_when_asked_for(self):
        self.serve(pdf=PDF)
        self.run_pdf("--out-dir", str(self.out))
        self.assertEqual("images", self.site.asked("GET", self.PATH)[0]["query"]["include"])
        self.assertNotIn("flyer-r4.pdf", self.names())

        self.site.requests.clear()
        code, out, err = self.run_pdf("--out-dir", str(self.out), "--with-pdf")
        self.assertEqual(0, code, err)
        self.assertEqual("both", self.site.asked("GET", self.PATH)[0]["query"]["include"])
        self.assertEqual(PDF, (self.out / "flyer-r4.pdf").read_bytes())
        self.assertIn("flyer-r4.pdf", out)

    def test_a_revision_and_a_resolution_are_sent_as_asked(self):
        self.serve(made(revision=3, dpi=120))
        code, _out, err = self.run_pdf("--revision", "3", "--dpi", "120", "--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual({"revision": 3, "dpi": 120}, self.site.asked("POST", self.PATH)[0]["body"])
        self.assertEqual("3", self.site.asked("GET", self.PATH)[0]["query"]["revision"])

    def test_the_pictures_go_to_a_folder_of_their_own_by_site_and_revision(self):
        self.serve()
        code, out, err = self.run_pdf()
        self.assertEqual(0, code, err)
        folder = self.sessions / "flyer-pages" / "127.0.0.1" / "r4"
        self.assertEqual(["page-1.png", "page-2.png", "page-3.png", "page-4.png"], self.names(folder))
        self.assertIn(str(folder), out)

    def test_an_answer_made_before_is_called_by_that_name(self):
        self.serve(made(cached=True))
        _code, out, _err = self.run_pdf("--out-dir", str(self.out))
        self.assertIn("already made", out)

    def test_pages_left_by_an_earlier_longer_flyer_are_removed(self):
        self.serve()
        self.run_pdf("--out-dir", str(self.out))
        self.site.routes.clear()
        self.serve(made(pages=[{"n": 1, "source": "design"}, {"n": 2, "source": "design"}]))
        (self.out / "notes.txt").write_text("mine", encoding="utf-8")
        code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual(["notes.txt", "page-1.png", "page-2.png"], self.names())
        self.assertNotIn("page-3", out)

    def test_json_gives_the_files_and_no_picture_data(self):
        self.serve()
        code, out, err = self.run_pdf("--out-dir", str(self.out), "--json")
        self.assertEqual(0, code, err)
        data = json.loads(out)
        self.assertEqual(4, data["page_count"])
        self.assertEqual(str(self.out / "page-1.png"), data["files"]["pages"]["1"])
        self.assertNotIn("png", json.dumps(data["images"]))

    # -- the warnings, in words --------------------------------------------------------

    def test_warnings_are_said_in_plain_words(self):
        self.serve(made(warnings=[
            {"code": "W-FL-PAGE-OVERFLOW", "message": "The PDF has more pages than the design."},
            {"code": "W-FL-ATTACHMENT-SKIPPED", "message": "Attachment skipped.", "attachment_id": 99,
             "attachment_name": "Old plan"},
            {"code": "W-FL-NO-MAP", "message": "No stored map."},
            {"code": "W-FL-NO-FRAME", "message": "No frame.", "attachment_id": 5, "attachment_name": "Floor plan"},
            {"code": "W-FL-SOMETHING-NEW", "message": "CRE Cloud says something new."},
        ]))
        _code, out, _err = self.run_pdf("--out-dir", str(self.out))
        self.assertNotIn("no warnings", out.lower())
        self.assertIn("did not fit", out)
        self.assertIn('"Old plan"', out)
        self.assertIn("left out", out)
        self.assertIn("map", out)
        self.assertIn('"Floor plan"', out)
        self.assertIn("CRE Cloud says something new.", out)
        for code in ("W-FL-PAGE-OVERFLOW", "W-FL-ATTACHMENT-SKIPPED", "W-FL-NO-MAP", "W-FL-NO-FRAME"):
            self.assertNotIn(code, out, "a warning code was printed in place of words")

    # -- busy and rate limited ---------------------------------------------------------

    def test_when_the_engine_is_busy_it_waits_and_asks_again(self):
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_busy", "message": "Busy.",
                                              "retry_after": 3}, {"Retry-After": "3"})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual([3], self.sleeps)
        self.assertIn("PDF engine is busy", err)
        self.assertIn("trying again", err)
        self.assertEqual(2, len(self.site.asked("POST", self.PATH)))

    def test_it_waits_as_long_as_it_is_told_to_within_reason(self):
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_rate_limited", "message": "Slow down.",
                                              "retry_after": 45})
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_rate_limited", "message": "Slow down.",
                                              "retry_after": 9000})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        self.run_pdf("--out-dir", str(self.out))
        self.assertEqual([45, crecs_preview.MAX_WAIT_SECONDS], self.sleeps)

    def test_it_takes_the_wait_from_the_header_when_the_body_has_none(self):
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_busy", "message": "Busy."},
                     {"Retry-After": "7"})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        self.run_pdf("--out-dir", str(self.out))
        self.assertEqual([7], self.sleeps)

    def test_it_waits_a_few_seconds_when_nobody_says_how_long(self):
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_busy", "message": "Busy."})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        self.run_pdf("--out-dir", str(self.out))
        self.assertEqual([crecs_preview.DEFAULT_WAIT_SECONDS], self.sleeps)

    def test_picture_download_that_is_rate_limited_waits_too(self):
        meta = made()
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 429, {"code": "crecs_preview_rate_limited", "message": "Too many requests.",
                                             "retry_after": 2})
        self.site.on("GET", self.PATH, 200, fetched(meta))
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual([2], self.sleeps)

    def test_the_number_of_tries_is_small(self):
        # Every wait is up to MAX_WAIT_SECONDS: a bound that is not small is a minute of
        # silence for each extra try.
        self.assertTrue(2 <= crecs_preview.MAX_WAITS <= 6, crecs_preview.MAX_WAITS)
        self.assertLessEqual(crecs_preview.MAX_WAIT_SECONDS, 60)

    def test_busy_too_many_times_is_a_plain_failure(self):
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_busy", "message": "Busy.",
                                              "retry_after": 2})
        code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(2, code)
        self.assertEqual(crecs_preview.MAX_WAITS, len(self.sleeps))
        self.assertEqual(crecs_preview.MAX_WAITS + 1, len(self.site.asked("POST", self.PATH)))
        self.assertIn("stayed busy", err)
        self.assertIn("try again", err)
        self.assertNotIn("Traceback", err)
        self.assertEqual("", out)
        self.assertFalse(self.out.exists() and any(self.out.iterdir()), "pictures were written")

    # -- the hour's allowance ----------------------------------------------------------

    HOURLY = {"code": "crecs_preview_rate_limited", "retry_after": 1800,
              "message": "You have asked CRE Cloud for 30 exact PDFs this hour, the most one person may "
                         "across all their previews. Wait, then ask again."}

    def test_the_hours_allowance_is_reported_not_waited_for(self):
        # retry_after is up to 3600: a command that slept 60 s and asked again would only be
        # refused again, four times, and say the engine was busy. It says what is true, at once.
        self.site.on("POST", self.PATH, 429, dict(self.HOURLY), {"Retry-After": "1800"})
        code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(2, code)
        self.assertEqual([], self.sleeps, "it waited for an hour's allowance")
        self.assertEqual(1, len(self.site.asked("POST", self.PATH)))
        self.assertEqual([], self.site.asked("GET", self.PATH))
        self.assertIn("this hour", err)
        self.assertIn("30 minutes", err)
        self.assertNotIn("busy", err.lower())
        self.assertNotIn("Traceback", err)
        self.assertNotIn("crecs_preview_rate_limited", err)
        self.assertEqual("", out)
        self.assertFalse(self.out.exists() and any(self.out.iterdir()), "pictures were written")

    def test_an_hourly_wait_is_known_by_its_length_too(self):
        # A site in another language words the refusal differently; a wait longer than the
        # command would ever wait is no short pause whatever the words.
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_rate_limited", "message": "Demasiadas.",
                                              "retry_after": 3000})
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(2, code)
        self.assertEqual([], self.sleeps)
        self.assertEqual(1, len(self.site.asked("POST", self.PATH)))
        self.assertIn("50 minutes", err)

    def test_the_wait_is_said_in_whole_minutes_rounded_up(self):
        for seconds, words in ((61, "2 minutes"), (3600, "60 minutes"), (125, "3 minutes")):
            with self.subTest(seconds=seconds):
                self.site.routes.clear()
                self.site.on("POST", self.PATH, 429, dict(self.HOURLY, retry_after=seconds))
                _code, _out, err = self.run_pdf("--out-dir", str(self.out))
                self.assertIn(words, err)
        self.assertEqual([], self.sleeps)

    def test_an_hourly_refusal_with_no_time_still_says_what_to_do(self):
        payload = dict(self.HOURLY)
        del payload["retry_after"]
        self.site.on("POST", self.PATH, 429, payload)
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(2, code)
        self.assertEqual([], self.sleeps)
        self.assertIn("this hour", err)
        self.assertIn("up to an hour", err)

    def test_the_minutes_allowance_is_still_waited_for(self):
        # The per-minute budget (and the polling one) answers the same code with a wait of a
        # minute at most: that one is worth waiting for.
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_rate_limited", "retry_after": 30,
                                              "message": "This preview has asked CRE Cloud for 12 exact PDFs "
                                                         "this minute, the most it may. Wait, then ask again."})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual([30], self.sleeps)

    def test_the_pdf_engines_own_limit_is_still_waited_for_whatever_it_asks(self):
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_rate_limited", "message": "Slow down.",
                                              "retry_after": 3000})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertEqual([crecs_preview.MAX_WAIT_SECONDS], self.sleeps)

    # -- a fresh PDF, and how old the one shown is ---------------------------------------

    def test_without_fresh_nothing_about_it_is_sent(self):
        self.serve()
        self.run_pdf("--out-dir", str(self.out))
        self.assertEqual({"dpi": 96}, self.site.asked("POST", self.PATH)[0]["body"])

    def test_fresh_asks_for_a_new_pdf_with_the_property_asked_for_anew(self):
        self.serve()
        code, _out, err = self.run_pdf("--fresh", "--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        body = self.site.asked("POST", self.PATH)[0]["body"]
        self.assertIs(True, body["fresh"])
        self.assertEqual(96, body["dpi"])

    def test_fresh_goes_with_a_revision_and_a_resolution(self):
        self.serve(made(revision=3, dpi=120))
        self.run_pdf("--fresh", "--revision", "3", "--dpi", "120", "--out-dir", str(self.out))
        self.assertEqual({"revision": 3, "dpi": 120, "fresh": True}, self.site.asked("POST", self.PATH)[0]["body"])

    def test_fresh_is_asked_again_when_the_engine_was_busy(self):
        meta = made()
        self.site.on("POST", self.PATH, 429, {"code": "crecs_preview_flyer_busy", "message": "Busy.", "retry_after": 2})
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        self.run_pdf("--fresh", "--out-dir", str(self.out))
        self.assertEqual([True, True], [r["body"].get("fresh") for r in self.site.asked("POST", self.PATH)])

    def test_a_pdf_made_over_a_minute_ago_says_how_long_ago(self):
        for age, words in ((61, "1 minute ago"), (420, "7 minutes ago"), (600, "10 minutes ago"),
                           (7300, "2 hours ago"), (200000, "2 days ago")):
            with self.subTest(age=age):
                self.site.routes.clear()
                self.serve(made(cached=True, age_seconds=age))
                code, out, err = self.run_pdf("--out-dir", str(self.out))
                self.assertEqual(0, code, err)
                self.assertIn("This PDF was made %s; ask for a fresh one if something changed in CRE Cloud." % words, out)

    def test_a_pdf_made_a_minute_ago_or_less_says_nothing_about_its_age(self):
        for age in (0, 1, 45, 60):
            with self.subTest(age=age):
                self.site.routes.clear()
                self.serve(made(age_seconds=age))
                _code, out, _err = self.run_pdf("--out-dir", str(self.out))
                self.assertNotIn(" ago", out)
                self.assertNotIn("ask for a fresh one", out)

    def test_a_site_that_does_not_say_the_age_is_not_made_to(self):
        self.serve(made(cached=True))  # an older plugin: no age_seconds
        code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertNotIn("ago", out)

    def test_the_age_is_the_stored_ones_when_the_two_answers_differ(self):
        meta = made(cached=True, age_seconds=400)
        stored = fetched(meta)
        stored["age_seconds"] = 410
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, stored)
        _code, out, _err = self.run_pdf("--out-dir", str(self.out))
        self.assertIn("made 6 minutes ago", out)

    def test_the_age_is_in_the_json_too(self):
        self.serve(made(cached=True, age_seconds=420))
        code, out, err = self.run_pdf("--out-dir", str(self.out), "--json")
        self.assertEqual(0, code, err)
        self.assertEqual(420, json.loads(out)["age_seconds"])

    def test_a_site_that_ignored_fresh_is_told_to_the_assistant(self):
        # An older plugin does not know `fresh` and would answer the stored PDF: the assistant
        # must not believe it has a new one.
        self.serve(made(cached=True, age_seconds=300))
        code, out, err = self.run_pdf("--fresh", "--out-dir", str(self.out))
        self.assertEqual(0, code, err)
        self.assertIn("did not make a new PDF", out)
        self.assertIn("made 5 minutes ago", out)

    def test_a_new_pdf_that_was_asked_for_is_not_called_old(self):
        self.serve(made(cached=False, age_seconds=2))
        _code, out, _err = self.run_pdf("--fresh", "--out-dir", str(self.out))
        self.assertNotIn("did not make a new PDF", out)
        self.assertNotIn("already made", out)

    def test_fresh_is_a_flag_of_pdf_only(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
            crecs_preview.main(["state", "--session-file", str(self.file), "--fresh"])
        self.assertEqual(2, caught.exception.code)

    # -- what goes wrong ---------------------------------------------------------------

    def test_nothing_stored_for_the_revision_is_said_plainly(self):
        meta = made()
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 404, {"code": "crecs_preview_flyer_pdf_none",
                                             "message": "No exact PDF has been made of revision 4 yet: make it first."})
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(2, code)
        self.assertIn("revision 4", err)
        self.assertIn("try again", err)
        self.assertNotIn("crecs_preview_flyer_pdf_none", err)

    def test_a_flyer_with_no_property_says_how_to_choose_one(self):
        self.site.on("POST", self.PATH, 409, {"code": "crecs_preview_no_property",
                                              "message": "This preview has no property selected."})
        code, _out, err = self.run_pdf()
        self.assertEqual(2, code)
        self.assertIn("property", err)

    def test_a_design_that_does_not_validate_lists_its_findings(self):
        self.site.on("POST", self.PATH, 422, {
            "code": "crecs_preview_invalid", "message": "This revision's design does not validate.",
            "findings": [{"level": "error", "code": "E-FL-VALUE", "node": "fl1a0042", "element": "fl1a0042",
                          "message": "A photo's height leaves no room."}]})
        code, _out, err = self.run_pdf()
        self.assertEqual(2, code)
        self.assertIn("E-FL-VALUE", err)
        self.assertIn("fl1a0042", err)

    def test_creclouds_own_refusal_lists_what_it_found(self):
        self.site.on("POST", self.PATH, 422, {
            "code": "crecs_preview_flyer_rejected", "message": "CRE Cloud refused the flyer the plugin made.",
            "findings": [{"code": "E-FL-URL", "message": "Image address is not allowed.", "source": "api",
                          "element": "", "where": {"part": "pages_html", "near": "<img"}}]})
        code, _out, err = self.run_pdf()
        self.assertEqual(2, code)
        self.assertIn("CRE Cloud refused the flyer", err)
        self.assertIn("Image address is not allowed.", err)

    def test_api_problems_come_in_the_plugins_plain_words(self):
        for status, code, message in (
                (502, "crecs_preview_flyer_api", "CRE Cloud could not be reached. Try again in a moment."),
                (503, "crecs_preview_no_api", "This site is not connected to CRE Cloud."),
                (504, "crecs_preview_flyer_timeout", "CRE Cloud took too long to make the PDF.")):
            with self.subTest(status=status):
                self.site.routes.clear()
                self.site.on("POST", self.PATH, status, {"code": code, "message": message})
                exit_code, out, err = self.run_pdf("--out-dir", str(self.out))
                self.assertEqual(2, exit_code)
                self.assertIn(message, err)
                self.assertEqual("", out)

    def test_a_dead_session_says_how_to_renew_it(self):
        self.site.on("POST", self.PATH, 401, {"code": "crecs_preview_unauthorised", "message": "Wrong token."})
        code, _out, err = self.run_pdf()
        self.assertEqual(2, code)
        self.assertIn("New link", err)

    # -- the plugin's newer refusals, in plain words -------------------------------------

    def refused(self, status, code, message, **extra):
        self.site.routes.clear()
        self.site.on("POST", self.PATH, status, dict({"code": code, "message": message}, **extra))
        exit_code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(2, exit_code, "a refusal by the site exits 2")
        self.assertEqual("", out)
        self.assertEqual([], self.sleeps, "a refusal that is not a busy engine is not waited for")
        self.assertEqual(1, len(self.site.asked("POST", self.PATH)))
        self.assertNotIn("Traceback", err)
        return err

    def test_a_flyer_preview_needs_a_site_administrator(self):
        err = self.refused(403, "crecs_preview_forbidden",
                           "Previewing a flyer needs a WordPress administrator: ask one to start the flyer "
                           "preview, or to make you one.")
        self.assertIn("Only a site administrator can use the flyer preview", err)
        self.assertIn("sign in", err.lower())
        self.assertIn("administrator account", err)
        # It is not a dead link: the new-link advice for a changed token would send the person
        # to the wrong place.
        self.assertNotIn("New link", err)

    def test_other_forbidden_answers_are_left_as_they_were(self):
        err = self.refused(403, "crecs_preview_forbidden", "Publishing the search page needs a WordPress administrator.")
        self.assertIn("Publishing the search page needs a WordPress administrator.", err)
        self.assertNotIn("Only a site administrator can use the flyer preview", err)

    def test_too_many_flyer_previews_says_to_close_one(self):
        err = self.refused(409, "crecs_preview_too_many",
                           "You already have 3 flyer previews open, the most there can be at once.")
        self.assertIn("too many flyer previews", err)
        self.assertIn("Close one", err)
        self.assertIn("Template preview", err)

    def test_a_property_the_site_does_not_list_is_said_so(self):
        err = self.refused(403, "crecs_preview_forbidden_property", "That property is not one this site can list.")
        self.assertIn("not on this site's list", err)
        self.assertIn("property", err)
        self.assertNotIn("New link", err)

    def test_a_design_with_too_much_image_data_says_to_use_a_smaller_logo(self):
        err = self.refused(413, "crecs_preview_flyer_too_large",
                           "The flyer is too large to send to CRE Cloud: use fewer or smaller embedded images, "
                           "such as the logo.")
        self.assertIn("too much image data", err)
        self.assertIn("smaller logo", err)

    def test_the_new_refusals_never_carry_a_token_or_a_stack_trace(self):
        for status, code in ((403, "crecs_preview_forbidden"), (409, "crecs_preview_too_many"),
                             (403, "crecs_preview_forbidden_property"), (413, "crecs_preview_flyer_too_large")):
            with self.subTest(code=code):
                self.site.routes.clear()
                self.site.on("POST", self.PATH, status, {"code": code, "message": "No.", "token": TOKEN_FLYER})
                exit_code, out, err = self.run_pdf()
                self.assertEqual(2, exit_code)
                self.no_token(out, err)

    def test_a_resolution_outside_the_range_is_refused_before_asking(self):
        for dpi in ("50", "151", "abc"):
            with self.subTest(dpi=dpi):
                err = io.StringIO()
                with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
                    crecs_preview.main(["pdf", "--session-file", str(self.file), "--dpi", dpi])
                self.assertEqual(2, caught.exception.code)
                self.assertIn("72", err.getvalue())
        self.assertEqual([], self.site.requests)

    # -- every file is checked ---------------------------------------------------------

    def test_a_picture_that_is_not_a_png_is_not_saved(self):
        meta = made()
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta, png=lambda n: PNG if n != 2 else b"<html>oops</html>"))
        code, out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(3, code)
        self.assertIn("page 2", err)
        self.assertEqual("", out)
        self.assertFalse(self.out.exists() and any(self.out.iterdir()), "an unchecked picture was kept")

    def test_a_pdf_that_is_not_a_pdf_is_not_saved(self):
        self.serve(pdf=b"<html>not a pdf</html>")
        code, _out, err = self.run_pdf("--out-dir", str(self.out), "--with-pdf")
        self.assertEqual(3, code)
        self.assertIn("PDF", err)
        self.assertFalse((self.out / "flyer-r4.pdf").exists())
        self.assertFalse(self.out.exists() and any(self.out.iterdir()))

    def test_a_missing_pdf_is_not_a_silent_success(self):
        self.serve(pdf=None)
        code, _out, err = self.run_pdf("--out-dir", str(self.out), "--with-pdf")
        self.assertEqual(3, code)
        self.assertIn("PDF", err)

    def test_picture_data_that_is_not_base64_is_refused(self):
        meta = made()
        data = fetched(meta)
        data["images"][0]["png"] = "!!! not base64 !!!"
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, data)
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(3, code)
        self.assertIn("page 1", err)

    def test_a_page_the_site_could_not_give_back_is_said(self):
        meta = made()
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta, only=(1, 2, 4)))
        code, _out, err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(3, code)
        self.assertIn("page 3", err)

    def test_a_flyer_longer_than_the_pictures_it_gets_still_lists_every_page(self):
        pages = [{"n": n, "source": "design"} for n in range(1, 4)]
        meta = made(pages=pages)
        meta["images"] = meta["images"][:2]
        self.site.on("POST", self.PATH, 200, meta)
        self.site.on("GET", self.PATH, 200, fetched(meta))
        code, out, _err = self.run_pdf("--out-dir", str(self.out))
        self.assertEqual(0, code)
        self.assertIn("page 3", out)
        self.assertIn("no picture", out)
        self.assertEqual(["page-1.png", "page-2.png"], self.names())

    def test_an_attachment_named_with_any_letters_prints_through_a_pipe_that_is_not_utf8(self):
        # Windows gives a piped stdout its ANSI code page; an attachment is named by whoever
        # uploaded it, and the assistant reads the pipe as UTF-8.
        name = "Caf" + chr(0xE9) + " " + chr(0x2013) + " plan " + chr(0x1F600)
        self.serve(made(pages=[{"n": 1, "source": "attachment", "attachment_name": name,
                                "layout": "8.5x11", "global": False}]))
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", newline="\n")
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(io.StringIO()):
            code = crecs_preview.main(["pdf", "--session-file", str(self.file), "--out-dir", str(self.out)])
        stream.flush()
        self.assertEqual(0, code)
        self.assertIn('attachment "%s"' % name, raw.getvalue().decode("utf-8"))

    def test_a_home_folder_in_the_out_dir_is_expanded(self):
        self.serve()
        with mock.patch.dict(os.environ, {"HOME": self.dir, "USERPROFILE": self.dir}):
            code, _out, err = self.run_pdf("--out-dir", "~/flyer-here")
        self.assertEqual(0, code, err)
        self.assertTrue((Path(self.dir) / "flyer-here" / "page-1.png").is_file())

    def test_the_token_never_shows_whatever_the_server_says(self):
        self.site.on("POST", self.PATH, 500, {"code": "crecs_preview_storage", "message": "Failed.",
                                              "token": TOKEN_FLYER})
        code, out, err = self.run_pdf()
        self.assertEqual(2, code)
        self.no_token(out, err)


if __name__ == "__main__":
    unittest.main()
