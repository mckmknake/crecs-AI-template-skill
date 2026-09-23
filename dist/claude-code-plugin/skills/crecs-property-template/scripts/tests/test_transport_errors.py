"""F5: when the site answers with something unexpected, say what to do about it.

The rehearsal's symptom — `nodes.forEach is not a function` — came from browser code that
no longer exists, and the file half is covered by `read_json`. What was left is the
transport: `crecs_preview.py` talks to a WordPress site, and WordPress answers with an
HTML login page, a redirect, a maintenance page or a caching plugin's output far more
often than it answers with the JSON you asked for.

A `json.JSONDecodeError` traceback, or four hundred characters of raw HTML quoted as an
error message, tells the person nothing. These pin the four cases that actually happen,
against a real server rather than a mock, so the parsing is exercised end to end.
"""

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from crecs_preview import Client, Refused, Transport

LOGIN_PAGE = (
    "<!DOCTYPE html><html><head><title>Log In</title></head>"
    "<body class='login'><form name='loginform' id='loginform'>"
    "<input name='log'><input name='pwd'></form></body></html>"
)


class Handler(BaseHTTPRequestHandler):
    """Serves whatever the test asked for. `reply` is set per test."""

    reply = (200, "application/json", "{}")

    def _send(self):
        status, ctype, body = self.reply
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_DELETE = _send

    def log_message(self, *args):  # keep the test output readable
        pass


class TransportErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        cls.base = "http://127.0.0.1:%d" % cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def client(self):
        return Client(self.base, "ps_test", "token-test")

    def reply(self, status, ctype, body):
        Handler.reply = (status, ctype, body)

    # -- the four cases that actually happen ----------------------------------

    def test_an_html_page_with_a_200_is_not_a_traceback(self):
        # A login page served with 200 is the classic: json.loads raised straight
        # through the transport and the person saw a JSONDecodeError.
        self.reply(200, "text/html", LOGIN_PAGE)
        with self.assertRaises((Transport, Refused)) as caught:
            self.client().state()
        message = str(caught.exception).lower()
        # The requirement is that the message names what came back, not that it uses
        # any particular word for it — "the WordPress login page" is better than "HTML".
        self.assertTrue(
            any(w in message for w in ("html", "page")),
            "the message does not say what the site replied with: " + message,
        )
        self.assertNotIn("expecting value", message, "the JSON decoder's complaint leaked")
        self.assertNotIn("traceback", message)

    def test_a_non_html_non_json_body_is_quoted_briefly(self):
        self.reply(200, "text/plain", "upstream connect error " * 40)
        with self.assertRaises((Transport, Refused)) as caught:
            self.client().state()
        message = str(caught.exception)
        self.assertIn("upstream connect error", message)
        self.assertLess(len(message), 400, "the whole body was quoted")

    def test_a_login_page_says_to_sign_in_again(self):
        self.reply(200, "text/html", LOGIN_PAGE)
        with self.assertRaises((Transport, Refused)) as caught:
            self.client().state()
        message = str(caught.exception).lower()
        self.assertTrue(
            any(w in message for w in ("log in", "login", "sign in", "session")),
            "an HTML login page should point at signing in: " + message,
        )

    def test_html_in_an_error_body_is_not_quoted_raw(self):
        self.reply(500, "text/html", "<html><body>" + ("x" * 900) + "</body></html>")
        with self.assertRaises((Transport, Refused)) as caught:
            self.client().state()
        message = str(caught.exception)
        self.assertNotIn("xxxxxxxxxx", message, "raw HTML was quoted into the message")
        self.assertIn("500", message)

    def test_a_missing_rest_route_says_the_preview_is_not_enabled(self):
        # With the flag off the module registers nothing, so the namespace 404s with
        # WordPress's own message, which says nothing about this plugin.
        self.reply(404, "application/json", json.dumps({
            "code": "rest_no_route",
            "message": "No route was found matching the URL and request method.",
            "data": {"status": 404},
        }))
        with self.assertRaises(Refused) as caught:
            self.client().state()
        message = str(caught.exception).lower()
        self.assertTrue(
            any(w in message for w in ("not enabled", "turned on", "crecs_preview_enabled")),
            "a missing route should name the flag: " + message,
        )

    def test_a_stale_token_says_where_to_get_the_new_one(self):
        # Reissuing a viewer link rotates the token, so a session file can go stale
        # legitimately. The message should say that rather than implying a break-in.
        self.reply(401, "application/json", json.dumps({
            "code": "crecs_preview_unauthorised",
            "message": "Unknown session or wrong token.",
            "data": {"status": 401},
        }))
        with self.assertRaises(Refused) as caught:
            self.client().state()
        message = str(caught.exception).lower()
        self.assertIn("template preview", message)

    # -- and the ordinary path still works ------------------------------------

    def test_a_json_reply_is_returned_unchanged(self):
        self.reply(200, "application/json", json.dumps({"head": 3, "property": "x"}))
        self.assertEqual({"head": 3, "property": "x"}, self.client().state())

    def test_an_empty_body_is_an_empty_object(self):
        self.reply(200, "application/json", "")
        self.assertEqual({}, self.client().state())

    def test_a_json_error_keeps_its_code_and_message(self):
        self.reply(422, "application/json", json.dumps({
            "code": "crecs_preview_invalid",
            "message": "The document did not pass server-side validation.",
        }))
        with self.assertRaises(Refused) as caught:
            self.client().state()
        self.assertIn("crecs_preview_invalid", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
