#!/usr/bin/env python3
"""Preview transport for the CRECS property template — delivery 4.

Speaks the nine operations of the preview contract to a WordPress site running the
crecs preview module. Standard library only, offline except for the site itself, and
no dependency on any model vendor's API.

The session credential is read from a session file, never from the command line, so it
does not land in shell history or in a process list:

    ~/.crecs/preview-<host>.json   {"id": "...", "token": "...", "base": "https://..."}

or whatever --session-file points at. Write that file with the site's own
`open-session` step (see docs/crecs-template-studio/PREVIEW-CONNECT.md); this script
never asks for a password and never prints a token.

Usage:
    crecs_preview.py capabilities --base https://site
    crecs_preview.py state
    crecs_preview.py current --out doc.json
    crecs_preview.py apply --document doc.json [--key my-key]
    crecs_preview.py property <slug>
    crecs_preview.py undo
    crecs_preview.py export --out export.json
    crecs_preview.py close
    crecs_preview.py watch [--interval 2.5]

Exit codes: 0 success, 2 refused by the server (conflict, invalid, rate limited),
3 transport or configuration problem.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

CONTRACT = 1
DEFAULT_SESSION_DIR = Path.home() / ".crecs"


class Refused(Exception):
    """The server understood and said no."""

    def __init__(self, code: str, message: str, payload: dict):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.payload = payload


class Transport(Exception):
    """The request never got a verdict."""


def _ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if not insecure:
        return None
    # Local development sites use a certificate the machine does not trust. Allowed
    # only behind an explicit flag, and only worth using against a .local host.
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class Client:
    def __init__(self, base: str, session_id: str = "", token: str = "", insecure: bool = False):
        self.base = base.rstrip("/")
        self.session_id = session_id
        self.token = token
        self.insecure = insecure

    # -- plumbing ---------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self.base}/wp-json/crecs/preview/v1{path}"

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        url = self._url(path)
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=300, context=_ssl_context(self.insecure)) as resp:
                raw = resp.read().decode("utf-8") or "{}"
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    # A 200 that is not JSON is almost always WordPress serving a page
                    # where an API was asked for: an expired login, a maintenance
                    # screen, a caching plugin. Raising the decoder's complaint here
                    # produced a traceback about column 1.
                    raise Transport(f"{url}: {_describe_html(raw)}") from None
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8", "replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"code": f"http_{exc.code}", "message": _describe_html(raw)}
            raise Refused(
                payload.get("code", f"http_{exc.code}"),
                _explain(payload.get("code", ""), payload.get("message", ""), exc.code),
                payload,
            ) from None
        except urllib.error.URLError as exc:
            raise Transport(f"{url}: {exc.reason}") from None
        except TimeoutError:
            raise Transport(f"{url}: timed out") from None

    def _session_path(self, suffix: str = "") -> str:
        if not self.session_id:
            raise Transport("no session id — write a session file or pass --session-file")
        return f"/sessions/{urllib.parse.quote(self.session_id)}{suffix}"

    # -- the nine operations ---------------------------------------------

    def capabilities(self) -> dict:
        return self._call("GET", "/capabilities")

    def resume(self) -> dict:
        return self._call("GET", self._session_path())

    def current(self) -> dict:
        return self._call("GET", self._session_path("/revision"))

    def apply(self, document, base_revision: int, key: str) -> dict:
        return self._call(
            "POST",
            self._session_path("/revision"),
            {"base_revision": base_revision, "document": document, "idempotency_key": key},
        )

    def set_property(self, slug: str) -> dict:
        return self._call("PUT", self._session_path("/property"), {"property": slug})

    def state(self) -> dict:
        return self._call("GET", self._session_path("/state"))

    def undo(self) -> dict:
        return self._call("POST", self._session_path("/undo"))

    def export(self) -> dict:
        return self._call("GET", self._session_path("/export"))

    def close(self) -> dict:
        return self._call("DELETE", self._session_path())


#: Where a person goes to start a preview, reissue a link or take a fresh session file.
ADMIN_SCREEN = "WordPress -> CRE Cloud Solutions -> Template preview"


def _describe_html(raw: str) -> str:
    """Say what a non-JSON body is, instead of quoting it.

    Four hundred characters of markup is not an error message. What the person needs is
    which kind of page it was, because each kind has a different answer.
    """
    head = raw.lstrip()[:2000].lower()
    if not head.startswith("<"):
        snippet = " ".join(raw.split())[:120]
        return f"the site replied with something that is not JSON: {snippet!r}"
    if "loginform" in head or "wp-login" in head or "user_login" in head:
        return ("the site replied with the WordPress login page, so the session has "
                "expired — sign in again, then take a fresh session file from "
                + ADMIN_SCREEN)
    if "maintenance" in head or "briefly unavailable" in head:
        return "the site replied with its maintenance page; try again once it is back"
    return ("the site replied with an HTML page where JSON was expected, which usually "
            "means the request never reached the preview module")


def _explain(code: str, message: str, status: int) -> str:
    """Add the sentence that says what to do, for the failures that have an answer."""
    if code == "rest_no_route":
        return (f"{message} The preview module is not enabled on this site: it registers "
                "no routes until the crecs_preview_enabled option is set.")
    if code in ("crecs_preview_unauthorised", "crecs_preview_expired") or status in (401, 403):
        return (f"{message} If a new preview link was issued, the token changed with it "
                f"— take the current session file from {ADMIN_SCREEN}.")
    return message


def canonical_hash(content) -> str:
    """The same canonical hash the server computes: object keys sorted recursively."""

    def norm(v):
        if isinstance(v, dict):
            return {k: norm(v[k]) for k in sorted(v)}
        if isinstance(v, list):
            return [norm(i) for i in v]
        return v

    blob = json.dumps(norm(content), separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load_session(path: Path | None, base: str | None) -> tuple[str, str, str]:
    """Return (base, session_id, token) from a session file, without printing any."""
    if path is None:
        if base is None:
            raise Transport("pass --base or --session-file")
        candidates = sorted(DEFAULT_SESSION_DIR.glob("preview-*.json"))
        if not candidates:
            return base, "", ""
        path = candidates[-1]

    if not path.is_file():
        raise Transport(f"session file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Transport(f"session file unreadable: {exc}") from None

    for key in ("id", "token"):
        if not data.get(key):
            raise Transport(f"session file is missing '{key}'")

    return (base or data.get("base", "")), data["id"], data["token"]


def cmd_watch(client: Client, interval: float) -> int:
    """Print state transitions until interrupted. Used to confirm sync by eye."""
    seen = None
    while True:
        try:
            st = client.state()
        except Refused as exc:
            print(f"refused: {exc}", file=sys.stderr)
            return 2
        except Transport as exc:
            print(f"disconnected: {exc}", file=sys.stderr)
            time.sleep(min(interval * 4, 30))
            continue

        key = (st.get("ready_revision"), st.get("last_state"), st.get("property"))
        if key != seen:
            seen = key
            print(
                f"{time.strftime('%H:%M:%S')}  revision={st.get('ready_revision')} "
                f"state={st.get('last_state')} property={st.get('property')} "
                f"hash={str(st.get('ready_hash', ''))[:12]}"
            )
        time.sleep(interval)


def main(argv=None) -> int:
    # The shared flags live on a parent parser so they are accepted on either side of
    # the subcommand; argparse otherwise rejects them after it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base", help="site base URL, e.g. https://example.com")
    common.add_argument("--session-file", type=Path, help="path to the session file")
    common.add_argument("--insecure", action="store_true", help="skip TLS verification (local .local sites only)")
    common.add_argument("--json", action="store_true", help="print raw JSON")

    p = argparse.ArgumentParser(description="CRECS preview transport (delivery 4)", parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("capabilities", "resume", "state", "undo", "close"):
        sub.add_parser(name, parents=[common])

    cur = sub.add_parser("current", parents=[common])
    cur.add_argument("--out", type=Path, help="write the document here")

    ap = sub.add_parser("apply", parents=[common])
    ap.add_argument("--document", type=Path, required=True, help="JSON file: either an Elementor export or a bare content array")
    ap.add_argument("--base-revision", type=int, help="defaults to the current head")
    ap.add_argument("--key", help="idempotency key; defaults to a random one")

    pr = sub.add_parser("property", parents=[common])
    pr.add_argument("slug")

    ex = sub.add_parser("export", parents=[common])
    ex.add_argument("--out", type=Path, help="write the export here")

    wa = sub.add_parser("watch", parents=[common])
    wa.add_argument("--interval", type=float, default=2.5)

    args = p.parse_args(argv)

    try:
        if args.cmd == "capabilities":
            if not args.base:
                raise Transport("capabilities needs --base")
            client = Client(args.base, insecure=args.insecure)
            caps = client.capabilities()
            if caps.get("contract") != CONTRACT:
                print(
                    f"warning: site speaks contract {caps.get('contract')}, this client speaks {CONTRACT}",
                    file=sys.stderr,
                )
            print(json.dumps(caps, indent=1) if args.json else
                  "\n".join(f"{k:26} {v}" for k, v in caps.items() if not isinstance(v, (dict, list))))
            return 0

        base, sid, token = load_session(args.session_file, args.base)
        client = Client(base, sid, token, insecure=args.insecure)

        if args.cmd == "watch":
            return cmd_watch(client, args.interval)

        if args.cmd == "apply":
            raw = json.loads(args.document.read_text(encoding="utf-8"))
            document = raw.get("content", raw) if isinstance(raw, dict) else raw
            base_rev = args.base_revision
            if base_rev is None:
                base_rev = int(client.state().get("head", 0))
            key = args.key or f"cli-{uuid.uuid4().hex[:16]}"
            result = client.apply(document, base_rev, key)
            local = canonical_hash(document)
            if result.get("hash") and result["hash"] != local:
                print(
                    f"warning: server hash {result['hash'][:12]} differs from locally computed {local[:12]}",
                    file=sys.stderr,
                )
            out = result
        elif args.cmd == "current":
            out = client.current()
            if args.out:
                args.out.write_text(json.dumps(out["document"], indent=1), encoding="utf-8")
        elif args.cmd == "export":
            out = client.export()
            if args.out:
                args.out.write_text(json.dumps(out["document"], indent=1), encoding="utf-8")
                manifest = args.out.with_suffix(args.out.suffix + ".manifest.json")
                manifest.write_text(json.dumps(out["manifest"], indent=1), encoding="utf-8")
        elif args.cmd == "property":
            out = client.set_property(args.slug)
        elif args.cmd == "state":
            out = client.state()
        elif args.cmd == "resume":
            out = client.resume()
        elif args.cmd == "undo":
            out = client.undo()
        elif args.cmd == "close":
            out = client.close()
        else:  # pragma: no cover - argparse guarantees one of the above
            raise Transport(f"unknown command {args.cmd}")

        # A session token is never echoed, whatever the server returned.
        if isinstance(out, dict):
            out.pop("token", None)

        if args.json:
            print(json.dumps(out, indent=1))
        else:
            for k, v in out.items():
                if isinstance(v, (dict, list)):
                    print(f"{k:22} {json.dumps(v)[:120]}")
                else:
                    print(f"{k:22} {v}")
        return 0

    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        if exc.code == "crecs_preview_conflict" and "head" in exc.payload:
            print(f"  the current head is {exc.payload['head']}; re-read it and rebase", file=sys.stderr)
        for finding in (exc.payload.get("findings") or [])[:8]:
            if finding.get("level") == "error":
                print(f"  [{finding.get('code')}] {finding.get('element')}: {finding.get('message')}", file=sys.stderr)
        return 2
    except Transport as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
