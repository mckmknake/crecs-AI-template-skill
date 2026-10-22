#!/usr/bin/env python3
"""Preview transport for the CRECS property template — delivery 4.

Speaks the nine operations of the preview contract to a WordPress site running the
crecs preview module. Standard library only, offline except for the site itself, and
no dependency on any model vendor's API.

The session credential is read from a session file, never from the command line, so it
does not land in shell history or in a process list:

    ~/.crecs/preview-<host>.json          {"id": "...", "token": "...", "base": "https://..."}
    ~/.crecs/preview-<host>-search.json   the same, with "kind": "search"
    ~/.crecs/preview-<host>-flyer.json    the same, with "kind": "flyer"

One file per kind of preview, so a site's property page, search page and flyer can be open
at once. Or whatever --session-file points at. The site's Template preview screen shows
that file's text in a box when a preview starts or gets a new link; `connect` saves it,
from standard input or a file, after checking it with the site. This script never asks
for a password and never prints a token.

Which session a command uses: --session-file wins; then --kind (property, search or
flyer); then the command's own kind (`pdf` and `sent` are a flyer's, `options` and
`published` are the search page's); otherwise the one saved session that fits, and the command says which
it took. An older ~/.crecs/preview-<host>.json that holds a search page session is still
read as the search page's, and `connect` moves it to its new name.

Usage:
    crecs_preview.py connect [--from box.txt]   (the box's text on standard input)
    crecs_preview.py capabilities --base https://site
                                    (sends the site's saved session, when there is one, so the site
                                     can say whether CRE Cloud keeps the client's logos; never to
                                     another site)
    crecs_preview.py state
    crecs_preview.py current --out doc.json
    crecs_preview.py apply --document doc.json [--key my-key]
    crecs_preview.py property <slug>
    crecs_preview.py undo
    crecs_preview.py export --out export.json
    crecs_preview.py close
    crecs_preview.py watch [--interval 2.5]
    crecs_preview.py options        (a search page session: the site's types and brokers)
    crecs_preview.py media [--search logo]   (the site's images, newest first, with their numbers)
    crecs_preview.py published      (a search page session: is the layout on display live?)
    crecs_preview.py pdf [--revision N] [--dpi 96] [--out-dir DIR] [--with-pdf] [--fresh]
                                    (a flyer session: the exact PDF CRE Cloud's printer makes, as a
                                     picture of every page the assistant can open; --fresh makes it
                                     again whatever the site stored, with the property asked for anew:
                                     for when something changed in CRE Cloud)
    crecs_preview.py sent           (a flyer session: has the flyer been sent to CRE Cloud, and has CRE
                                     Cloud made it? A question only: sending the flyer is the Send
                                     button in the preview window, which only a person presses)

Exit codes: 0 success, 2 refused by the server (conflict, invalid, rate limited, busy),
3 transport or configuration problem (including a session that cannot be found or chosen).
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
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

#: The kinds of preview a site can have open. A property preview is the one with no `kind`
#: in its session file, which is how every session was saved before search and flyer ones.
KINDS = ("property", "search", "flyer")

#: What a person calls each kind, and the button that starts it in Template preview.
KIND_LABEL = {"property": "property page", "search": "search page", "flyer": "flyer"}
KIND_START = {"property": "Start preview", "search": "Start search page preview",
              "flyer": "Start flyer preview"}

#: The kind a command is about, for the commands that are about one. The others work on
#: whichever session they are given.
NATURAL_KIND = {"pdf": "flyer", "sent": "flyer", "options": "search", "published": "search"}

#: The exact PDF: how often a busy or rate-limited engine is asked again, and how long to
#: wait when it says nothing or asks for more than is reasonable.
MAX_WAITS = 4
DEFAULT_WAIT_SECONDS = 5
MAX_WAIT_SECONDS = 60

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PDF_SIGNATURE = b"%PDF-"


def pause(seconds: float) -> None:
    """Wait. A function of its own so a test can answer without sleeping."""
    time.sleep(seconds)


class Refused(Exception):
    """The server understood and said no."""

    def __init__(self, code: str, message: str, payload: dict, status: int = 0):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.payload = payload
        self.status = status


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
                payload = None
            if not isinstance(payload, dict):
                payload = {"code": f"http_{exc.code}", "message": _describe_html(raw)}
            # A busy or rate-limited answer says when to come back in a header too.
            retry = exc.headers.get("Retry-After") if exc.headers else None
            if retry and "retry_after" not in payload:
                payload["retry_after"] = retry
            raise Refused(
                payload.get("code", f"http_{exc.code}"),
                _explain(payload.get("code", ""), payload.get("message", ""), exc.code),
                payload,
                exc.code,
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
        """What the site says it can do. With a session (an id and its token) the site knows who
        is asking and tells what it keeps for someone who may edit templates (whether CRE Cloud has
        the client's logos) instead of "not known"; with none it is the public answer."""
        path = "/capabilities"
        if self.session_id and self.token:
            path += "?id=" + urllib.parse.quote(self.session_id)
        return self._call("GET", path)

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

    # -- flyer sessions ---------------------------------------------------

    def flyer_pdf_make(self, revision: int | None, dpi: int, fresh: bool = False) -> dict:
        """Ask for the exact PDF of a revision (the ready one when none is named), or the
        one already stored for it (the site keeps one for ten minutes). `fresh` makes it
        again whatever is stored, with the property asked for anew; it is sent only when it
        is true, so a site that does not know it never sees it. Answers the PDF's metadata,
        never its bytes."""
        body: dict = {"dpi": dpi}
        if revision is not None:
            body["revision"] = revision
        if fresh:
            body["fresh"] = True
        return self._call("POST", self._session_path("/flyer-pdf"), body)

    def flyer_pdf_get(self, revision: int, include: str) -> dict:
        """What is stored for a revision, with the page pictures (`images`) and the PDF
        (`both`) in base64."""
        query = urllib.parse.urlencode({"revision": revision, "include": include})
        return self._call("GET", self._session_path("/flyer-pdf") + "?" + query)

    def flyer_status(self) -> dict:
        """Whether CRE Cloud has a designed flyer for the property on display, how its making
        went, and whether it was made from the design on screen. A question only: a flyer is
        sent by the Send button in the preview window, which the plugin takes from a
        signed-in administrator and refuses a session's token."""
        return self._call("GET", self._session_path("/flyer-status"))

    # -- search page sessions ---------------------------------------------

    def search_options(self) -> dict:
        """The property types and brokers the site lists, by the names `offer` and
        `start_checked` use."""
        return self._call("GET", self._session_path("/search-options"))

    def media(self, search: str = "") -> dict:
        """The site's images, newest first, by the number a layout's `pin_image` takes;
        `search` keeps those whose title has those words."""
        query = "?" + urllib.parse.urlencode({"search": search}) if search else ""
        return self._call("GET", self._session_path("/media") + query)


#: Where a person goes to start a preview, reissue a link or take a fresh session file.
ADMIN_SCREEN = "WordPress -> CRE Cloud Solutions -> Template preview"


def published_answer(state: dict) -> dict:
    """Is the layout on display in a search page preview what the live page shows?

    Asked after the person says they pressed Publish. Only the preview's own button
    publishes, and a person can miss its answer, or an embedded browser can swallow the
    question it asks, so the assistant checks rather than assumes. The preview's state
    carries the live page's hash beside the ready revision's.
    """
    if state.get("kind") != "search" or "live_hash" not in state:
        return {"live": None,
                "say": "This is not a search page preview: a property template is imported "
                       "into Elementor, not published."}
    revision = state.get("ready_revision")
    ready = state.get("ready_hash") or ""
    if not ready:
        return {"live": False, "revision": revision,
                "say": "no: the preview has no layout ready yet, so there is nothing to publish."}
    if ready == state.get("live_hash"):
        return {"live": True, "revision": revision,
                "say": f"yes: the live search page shows revision {revision}, the layout on "
                       "display in the preview."}
    return {"live": False, "revision": revision,
            "say": f"no: the live search page does not show revision {revision}, the layout on "
                   "display in the preview. It has not been published."}


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


#: What the plugin says (422, `crecs_preview_flyer_map_unsupported`) to a flyer with a satellite or
#: hybrid map when this site's CRE Cloud is known not to make one: nothing was made or sent.
MAP_UNSUPPORTED_WORDS = (
    "This site's CRE Cloud cannot make an aerial map yet, so a flyer with a satellite or hybrid map "
    "cannot be made or sent. Use the road map instead, or ask for CRE Cloud to be updated.")


def _explain(code: str, message: str, status: int) -> str:
    """Add the sentence that says what to do, for the failures that have an answer."""
    if code == "rest_no_route":
        return (f"{message} The preview module is not enabled on this site: it registers "
                "no routes until the crecs_preview_enabled option is set.")
    # What a flyer preview adds. None of these is a dead link, so none gets the new-link
    # advice below: it would send the person to the wrong place.
    if code == "crecs_preview_forbidden" and "flyer" in message.lower():
        return ("Only a site administrator can use the flyer preview, and the person this preview "
                "belongs to is not one. Ask them to sign in to WordPress with an administrator "
                f"account, then start the flyer preview again in {ADMIN_SCREEN}.")
    if code == "crecs_preview_too_many":
        return ("There are too many flyer previews open at once. Close one in "
                f"{ADMIN_SCREEN}, then start the new one.")
    if code == "crecs_preview_forbidden_property":
        return ("That property is not on this site's list, so it cannot be shown in a preview. "
                "Choose one of the properties the site lists.")
    if code == "crecs_preview_flyer_too_large":
        return ("The design carries too much image data for CRE Cloud to take. Use a smaller logo "
                "(a PNG or JPEG of about 300 KB at most) or fewer images, then ask again.")
    if code == "crecs_preview_flyer_map_unsupported":
        # The plugin's own sentence is plain and says what to do; keep it as it is, and say it
        # anyway when a site sends none.
        return message or MAP_UNSUPPORTED_WORDS
    if code in ("crecs_preview_unauthorised", "crecs_preview_expired") or status in (401, 403):
        return (f"{message} If a new preview link was issued, the token changed with it "
                f"— in {ADMIN_SCREEN}, use New link on this session (or start a new one) "
                "and save the box it shows with `crecs_preview.py connect`.")
    return message


class SessionText(Exception):
    """What was handed to `connect` is not a preview session."""


def parse_session_text(text: str) -> dict:
    """The session file, from the text of the Template preview box.

    Whatever surrounds the box's JSON is ignored, so the text can come straight from
    the page. The result has the keys the site writes, and nothing else.
    """
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end < start:
        raise SessionText("that text holds no preview session: it has no { … } in it")
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        raise SessionText("that text is not a preview session: its { … } is not JSON") from None
    if not isinstance(data, dict):
        raise SessionText("that text is not a preview session")
    base, sid, token = data.get("base"), data.get("id"), data.get("token")
    url = urllib.parse.urlparse(base) if isinstance(base, str) else None
    if not url or url.scheme not in ("http", "https") or not url.hostname:
        raise SessionText("that session has no site address (base)")
    if not isinstance(sid, str) or not sid.strip():
        raise SessionText("that session has no id")
    if not isinstance(token, str) or not token.strip() or any(c.isspace() for c in token.strip()):
        raise SessionText("that session has no usable token")
    kind = data.get("kind", "property")
    if kind not in KINDS:
        raise SessionText(f"that session is for an unknown page kind: {kind!r}")
    session = {"base": base.strip().rstrip("/"), "id": sid.strip(), "token": token.strip()}
    if kind != "property":
        session["kind"] = kind
    return session


def session_kind(data: dict) -> str:
    """The kind a session file or box holds: a property preview has none written."""
    kind = data.get("kind") if isinstance(data, dict) else None
    return kind if kind in KINDS else "property"


def session_name(host: str, kind: str) -> str:
    """A session file's name: the property page's is the one every session had before
    there were other kinds, and the others carry their kind."""
    return f"preview-{host}.json" if kind == "property" else f"preview-{host}-{kind}.json"


def session_path(session: dict, folder: Path) -> Path:
    """Where a session is saved: one file per kind of preview, so a site's property page,
    search page and flyer do not replace one another."""
    host = urllib.parse.urlparse(session["base"]).hostname.lower()
    return folder / session_name(host, session_kind(session))


def _read_session_file(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def migrate_old_search_file(folder: Path, host: str) -> bool:
    """Before there was a flyer, a search page session was saved as preview-<host>.json,
    the name a property session still has. Move one to the search page's own name, so the
    next property session does not replace it; never over a search file already there."""
    old, new = folder / session_name(host, "property"), folder / session_name(host, "search")
    data = _read_session_file(old) if old.is_file() else None
    if data is None or session_kind(data) != "search" or new.exists():
        return False
    os.replace(old, new)
    return True


def cmd_connect(source: str | None, folder: Path, insecure: bool, as_json: bool, kind: str | None = None) -> int:
    """Check a session with its site, then save it where the other commands read it."""
    try:
        if source in (None, "-"):
            text = sys.stdin.read()
        else:
            text = Path(source).read_text(encoding="utf-8")
        session = parse_session_text(text)
    except (OSError, UnicodeDecodeError, SessionText) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 3

    held = session_kind(session)
    if kind and held != kind:
        print(f"refused: that box holds a {KIND_LABEL[held]} preview session, not a {KIND_LABEL[kind]} one",
              file=sys.stderr)
        return 3
    label = KIND_LABEL[held]
    host = urllib.parse.urlparse(session["base"]).hostname
    target = session_path(session, folder)

    # A session the site refuses is not saved: it would only replace one that works.
    unreachable = ""
    try:
        Client(session["base"], session["id"], session["token"], insecure=insecure).state()
    except Refused as exc:
        print(f"refused: the site did not accept this preview session: {exc}", file=sys.stderr)
        return 2
    except Transport as exc:
        unreachable = str(exc)

    folder.mkdir(parents=True, exist_ok=True)
    migrate_old_search_file(folder, host.lower())
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(json.dumps(session, indent=1) + "\n", encoding="utf-8")
    try:
        os.chmod(temp, 0o600)
    except OSError:
        pass
    os.replace(temp, target)

    if as_json:
        print(json.dumps({"connected": not unreachable, "host": host, "kind": held,
                          "session_file": str(target)}, indent=1))
    else:
        print(f"connected to {host}: the {label} preview. Session saved in {target}; "
              f"pass it as --session-file.")
    if unreachable:
        print(f"warning: saved, but the site could not be reached to check it: {unreachable}",
              file=sys.stderr)
        return 3
    return 0


def canonical_hash(content) -> str:
    """The same canonical hash the server computes: object keys sorted recursively."""

    def norm(v):
        if isinstance(v, dict):
            return {k: norm(v[k]) for k in sorted(v)}
        if isinstance(v, list):
            return [norm(i) for i in v]
        return v

    # ensure_ascii, because PHP's json_encode() escapes every non-ASCII character as
    # \uXXXX: written raw, any accented text hashed differently on the two sides.
    blob = json.dumps(norm(content), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def saved_sessions(folder: Path, base: str | None = None) -> list[dict]:
    """The sessions saved in a folder: path, host, kind. One a site and kind: when both
    the old name and the kind's own name hold a search page session, the kind's own."""
    host = urllib.parse.urlparse(base).hostname if base else None
    chosen: dict = {}
    for path in sorted(folder.glob("preview-*.json")):
        data = _read_session_file(path)
        if not data or not data.get("id") or not data.get("token"):
            continue
        site = (urllib.parse.urlparse(str(data.get("base", ""))).hostname or "").lower()
        if host and site != host.lower():
            continue
        kind = session_kind(data)
        key = (site, kind)
        if key not in chosen or path.name == session_name(site, kind):
            chosen[key] = {"path": path, "host": site, "kind": kind}
    return list(chosen.values())


def _no_session(kind: str | None, base: str | None) -> Transport:
    where = f" for {urllib.parse.urlparse(base).hostname}" if base else ""
    if kind is None:
        return Transport("pass --base or --session-file")
    return Transport(
        f"no {KIND_LABEL[kind]} preview session is saved on this computer{where}. "
        f"In {ADMIN_SCREEN} press {KIND_START[kind]}, then save the box it shows with "
        f"`crecs_preview.py connect`.")


def _which_session(found: list[dict]) -> Transport:
    hosts = sorted({entry["host"] for entry in found})
    kinds = [kind for kind in KINDS if any(entry["kind"] == kind for entry in found)]
    parts = []
    if len(hosts) > 1:
        parts.append("they are for more than one site (" + ", ".join(hosts) + "): "
                     "say which with --base https://<site>")
    if len(kinds) > 1:
        parts.append("they are for a " + ", a ".join(KIND_LABEL[k] for k in kinds) + " preview: "
                     "say which with --kind " + "|".join(kinds))
    parts.append("or pass --session-file")
    return Transport("more than one preview session is saved here, so none was guessed; "
                     + "; ".join(parts) + ".")


def _find_session_file(base, kind, natural, folder, announce):
    """The session file to use when none was named; None means 'no file, only --base'."""
    wanted = kind or natural
    found = saved_sessions(folder, base)
    if wanted:
        found = [entry for entry in found if entry["kind"] == wanted]
    if not found:
        if wanted is None and base is not None:
            return None
        raise _no_session(wanted, base)
    if len(found) > 1:
        raise _which_session(found)
    entry = found[0]
    if announce:
        announce(f"using the {KIND_LABEL[entry['kind']]} preview session saved for "
                 f"{entry['host']} ({entry['path']})")
    return entry["path"]


def load_session(path: Path | None, base: str | None, kind: str | None = None,
                 natural: str | None = None, folder: Path | None = None,
                 announce=None) -> tuple[str, str, str]:
    """Return (base, session_id, token) from a session file, without printing any.

    An explicit `path` is used as it is (naming a `kind` it does not hold is refused).
    Otherwise the session is the one saved for `kind`, or for the command's `natural`
    kind, or the only one saved; `announce` is told which, in words.
    """
    if path is None:
        path = _find_session_file(base, kind, natural, folder or DEFAULT_SESSION_DIR, announce)
        if path is None:
            return base, "", ""

    if not path.is_file():
        raise Transport(f"session file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Transport(f"session file unreadable: {exc}") from None

    for key in ("id", "token"):
        if not data.get(key):
            raise Transport(f"session file is missing '{key}'")

    if kind and session_kind(data) != kind:
        raise Transport(f"{path} holds a {KIND_LABEL[session_kind(data)]} preview session, "
                        f"not a {KIND_LABEL[kind]} one")

    return (base or data.get("base", "")), data["id"], data["token"]


def capabilities_session(base: str, path: Path | None, kind: str | None, folder: Path,
                         announce=None) -> tuple[str, str]:
    """The session the `capabilities` command sends, as (id, token); ("", "") when it sends none.

    The site tells someone who holds a valid session more than it tells a stranger (whether CRE
    Cloud keeps the client's logos), so the command sends the saved one. It never stops to ask
    which: any session of a site says the same, so it takes the one of the wanted `kind`, else
    the first by kind. A session goes only to the site that issued it: one for another address is
    left out, and `announce` says so. A file that was named and cannot be used is an error, as for
    every command; one only found in the folder and unusable is passed over.
    """
    want = (urllib.parse.urlparse(base).hostname or "").lower()
    explicit = path is not None
    if path is None:
        found = [e for e in saved_sessions(folder, base) if not kind or e["kind"] == kind]
        if not found:
            return "", ""
        path = min(found, key=lambda e: KINDS.index(e["kind"]))["path"]
    elif not path.is_file():
        raise Transport(f"session file not found: {path}")

    data = _read_session_file(path)
    if not data or not data.get("id") or not data.get("token"):
        if explicit:
            raise Transport(f"session file unreadable or incomplete: {path}")
        return "", ""
    if explicit and kind and session_kind(data) != kind:
        raise Transport(f"{path} holds a {KIND_LABEL[session_kind(data)]} preview session, "
                        f"not a {KIND_LABEL[kind]} one")
    site = (urllib.parse.urlparse(str(data.get("base", ""))).hostname or "").lower()
    if site and want and site != want:
        if announce:
            announce(f"not sending the session in {path} to {want}: it is for {site}")
        return "", ""
    return str(data["id"]), str(data["token"])


# ---------------------------------------------------------------------------------------
# a flyer, in words
#
# What these print goes to the assistant, who tells a person who owns a property website
# what it means: so a revision is a number and everything else is a sentence, and a
# session token is never in any of it.
# ---------------------------------------------------------------------------------------

_LATEST_CHANGE = {
    "ready": "drawn and ready",
    "rejected": "refused by the plugin's checks, so the preview kept the one before it",
    "render_failed": "could not be drawn",
    "received": "still being prepared",
    "validated": "still being prepared",
}

_FAILED_CHANGE = {
    "validation": "was refused by the plugin's checks",
    "data": "was stopped by a problem with the property's data",
    "render": "could not be drawn",
}

#: How CRE Cloud names where an attachment goes, in words.
_ATTACHMENT_PLACE = {
    "8.5x11 - inside layout": "framed by the design's header and footer, portrait",
    "8.5x11 - inside layout landscape": "framed by the design's header and footer, landscape",
    "8.5x11": "on its own Letter page, with no header or footer",
    "11x17 - landscape entire page": "on its own Tabloid landscape page",
    "11x17 - portrait": "on its own Tabloid portrait page",
}


def _plural(count: int, word: str) -> str:
    return f"{count} {word}{'' if count == 1 else 's'}"


def flyer_state_text(state: dict) -> str:
    """A flyer preview's state as sentences, instead of a column of keys and values."""
    prop = state.get("property") or ""
    lines = ["This is a flyer preview, showing the property " + prop + "." if prop
             else "This is a flyer preview with no property chosen yet."]
    shown = f"On display: revision {state.get('ready_revision')}"
    fingerprint = str(state.get("ready_hash") or "")[:12]
    lines.append(shown + (f" (design {fingerprint})" if fingerprint else "") + ".")
    latest = state.get("last_state")
    if latest in _LATEST_CHANGE:
        lines.append(f"Latest change: revision {state.get('last_revision')}, {_LATEST_CHANGE[latest]}.")
    failed = [f for f in (state.get("failures") or []) if isinstance(f, dict)]
    if failed:
        lines.append("Changes that did not go through: " + "; ".join(
            f"revision {f.get('revision')} {_FAILED_CHANGE.get(f.get('class'), 'did not work')}" for f in failed) + ".")
    else:
        lines.append("No change has failed.")
    if state.get("expires_at"):
        lines.append(f"The preview ends at {state['expires_at']} (UTC).")
    return "\n".join(lines)


def flyer_design_text(current: dict, saved: Path | None = None) -> str:
    """The flyer design a preview shows, in a line or two."""
    document = current.get("document") if isinstance(current.get("document"), dict) else {}
    manifest = current.get("manifest") if isinstance(current.get("manifest"), dict) else {}
    content = document.get("content") if isinstance(document.get("content"), list) else []
    root = content[0] if content and isinstance(content[0], dict) else {}
    settings = root.get("settings") if isinstance(root.get("settings"), dict) else {}
    pages = sum(1 for n in root.get("elements") or []
                if isinstance(n, dict) and n.get("widgetType") == "crecs_flyer_page")
    title = document.get("title")
    line = "Flyer design" + (f' "{title}"' if title else "") + \
        f": {settings.get('orientation') or 'landscape'}, {_plural(pages, 'designed page')}"
    if manifest.get("revision") is not None:
        line += f", revision {manifest['revision']}"
    lines = [line + "."]
    if manifest.get("property_previewed"):
        lines.append(f"Shown with the property {manifest['property_previewed']}.")
    if saved:
        lines.append(f"Saved to {saved}.")
    return "\n".join(lines)


def page_words(page: dict) -> str:
    """What one page of the PDF is: a designed page, or an attachment and where it sits."""
    if page.get("source") != "attachment":
        return "designed page"
    name = page.get("attachment_name")
    what = ("company-wide attachment" if page.get("global") else "attachment") + (f' "{name}"' if name else "")
    layout = str(page.get("layout") or "")
    place = _ATTACHMENT_PLACE.get(layout.strip().lower()) or (f"layout {layout}" if layout else "")
    return what + (f", {place}" if place else "")


#: Why CRE Cloud printed the street map where a satellite or hybrid one was designed
#: (`reason` of W-FL-MAP-FALLBACK), in words a person can follow.
_MAP_FALLBACK_REASON = {
    "no_key": "CRE Cloud has no map key to make it with",
    "google_error": "Google, which draws the satellite pictures, could not make this one",
    "timeout": "CRE Cloud ran out of time making it",
    "no_imagery": "there are no satellite pictures of that place at that zoom (a smaller zoom number "
                  "may help)",
}


def warning_words(warning: dict) -> str:
    """One warning CRE Cloud gave about the PDF, as a sentence about the page."""
    code, message = warning.get("code"), str(warning.get("message") or "")
    name = warning.get("attachment_name")
    named = f'"{name}"' if name else "an attachment"
    if code == "W-FL-PAGE-OVERFLOW":
        return ("something did not fit on a designed page and ran onto an extra page: make that "
                "page's content smaller, or move part of it to another page")
    if code == "W-FL-ATTACHMENT-SKIPPED":
        return f"the attachment {named} could not be used, so it was left out of the PDF"
    if code == "W-FL-NO-MAP":
        if warning.get("reason") == "address_hidden":
            return ("a map block shows nothing, on purpose: the property hides its address, and a map "
                    "would give it away")
        return ("a map block shows nothing: CRE Cloud has no map picture for this property "
                "(a hidden address never gets one)")
    if code == "W-FL-MAP-FALLBACK":
        why = _MAP_FALLBACK_REASON.get(warning.get("reason")) \
            if isinstance(warning.get("reason"), str) else None
        return ("a map block could not be made as the satellite picture that was designed, so the flyer "
                "is showing the street map instead: " + (why or "CRE Cloud could not make it"))
    if code == "W-FL-MAP-OVERLAY-SKIPPED":
        count = warning.get("skipped")
        if isinstance(count, int) and not isinstance(count, bool) and count >= 1:
            return (f"{_plural(count, 'thing')} drawn on the property could not be drawn on the map, so "
                    f"{'it is' if count == 1 else 'they are'} missing from it")
        return ("some of the things drawn on the property could not be drawn on the map, so they are "
                "missing from it")
    if code == "W-FL-NO-FRAME":
        return (f"the design has no frame for the attachment {named}, so it sits alone on its page, "
                "without the design's header and footer")
    if code == "W-FL-IMAGE-LOAD":
        return "a picture could not be loaded, so it is missing or broken in the flyer"
    return message or f"CRE Cloud reported {code or 'a problem'}"


#: The kinds of map the flyer printer knows, in the order they are told, with what a person calls
#: each: `road` is the street map; the other two are the aerial ones.
_MAP_KINDS = (("road", "street map"), ("satellite", "satellite map"),
              ("hybrid", "satellite map with street names"))


def map_types_words(value) -> str:
    """The `capabilities` line about the aerial maps, from the plugin's `flyer_map_types`.

    The plugin gives a list of the kinds CRE Cloud makes, or null when it does not know:
    nothing was cached yet for someone who may not ask, CRE Cloud predates aerial maps or
    could not be reached. A list is read as the plugin reads it (a name it does not know is
    dropped); one with no satellite or hybrid in it is a site that makes the street map only,
    where a flyer asking for an aerial map is refused.
    """
    if not isinstance(value, list):
        return ("not known: CRE Cloud has not said whether it can make satellite maps for this site. "
                "Offer the street map; if the person wants a satellite one, make the exact PDF and "
                "check that the picture really is a satellite map")
    made = [words for kind, words in _MAP_KINDS if kind in value]
    if not any(kind in value for kind in ("satellite", "hybrid")):
        return ("street map only: CRE Cloud cannot make satellite maps for this site yet, so a flyer "
                "asking for one is refused. Offer the street map, or ask whoever looks after CRE Cloud "
                "to have it updated")
    return ("available: " + ", ".join(made) + ". CRE Cloud makes the satellite ones when it prints the "
            "flyer, so they show only in the exact PDF")


def brand_logos_words(value) -> str:
    """The `capabilities` line about the client's logos kept in CRE Cloud, from the plugin's
    `brand_logos`: `{company, flyer}`, each true or false, or null when that is not known (CRE
    Cloud could not be reached, it predates the logos, or a public call read an empty cache).

    Each logo is read by itself: anything but true or false is not known. A site whose plugin
    predates the logos sends no `brand_logos` at all, and the caller then prints no line.
    """
    got = value if isinstance(value, dict) else {}
    company, flyer = (got.get(key) if isinstance(got.get(key), bool) else None for key in ("company", "flyer"))
    follows = ("It follows any change made in CRE Cloud by itself: a page shows the new logo within about "
               "ten minutes (longer if the site keeps its pages in a cache), a flyer when it is sent again "
               "(give it ten minutes after the change) or when the plugin refreshes it by itself, which it "
               "does for a few flyers a day")
    if company is True and flyer is True:
        return ("available: CRE Cloud keeps the company logo and a flyer logo for this site, so a template "
                "can show either one instead of an uploaded picture. " + follows)
    if company is False and flyer is False:
        return ("none: CRE Cloud keeps neither a company logo nor a flyer logo for this site, so use the "
                "upload route for a logo, or have the person add theirs in CRE Cloud first")
    if company is None and flyer is None:
        return ("not known: CRE Cloud has not said whether it keeps a company logo or a flyer logo for this "
                "site. Use the upload route; if the person wants the logo kept in CRE Cloud, try it and look "
                "at the preview to see whether it shows")
    if company is True and flyer is False:
        return ("company logo only: CRE Cloud keeps the company logo but no flyer logo, so a template can "
                "show the company logo instead of an uploaded picture, and a flyer needs the upload route "
                "for any other logo. " + follows)
    if company is False and flyer is True:
        return ("flyer logo only: CRE Cloud keeps a flyer logo but no company logo, so a flyer can show the "
                "flyer logo, and a page needs the upload route for the company's logo. " + follows)
    status = {True: "available", False: "none kept", None: "not known"}
    return (f"company logo {status[company]}, flyer logo {status[flyer]}. Use a logo kept in CRE Cloud "
            "only where it is available, and the upload route for the other. " + follows)


class Busy(Exception):
    """The PDF engine stayed busy, or at its limit, through every try."""


class HourlyLimit(Exception):
    """The person has used the hour's allowance of exact PDFs: no wait here would help."""

    def __init__(self, seconds: int | None):
        super().__init__("the hour's allowance of exact PDFs is used up")
        self.seconds = seconds


def _asked_seconds(payload: dict) -> int | None:
    """The wait the answer asks for, in whole seconds; None when it asks for none."""
    try:
        return int(float(payload.get("retry_after")))
    except (TypeError, ValueError, OverflowError):
        return None


def wait_seconds(payload: dict) -> int:
    """How long to wait before asking again: what the answer says, within reason."""
    seconds = _asked_seconds(payload)
    if seconds is None:
        return DEFAULT_WAIT_SECONDS
    return max(1, min(seconds, MAX_WAIT_SECONDS))


def is_hourly_limit(exc: Refused) -> bool:
    """Is this 429 the allowance for the hour, rather than a pause of a minute at most?

    The site answers both with `crecs_preview_rate_limited`: the minute's budget (a session may
    make so many a minute) and the hour's (one person, all their previews together), whose wait
    is up to 3600 seconds. The hour's says so in its words, and asks for longer than this
    script ever waits, whichever language the words are in.
    """
    if exc.code != "crecs_preview_rate_limited":
        return False
    asked = _asked_seconds(exc.payload)
    if asked is not None and asked > MAX_WAIT_SECONDS:
        return True
    return re.search(r"\bthis hour\b", str(exc.payload.get("message") or ""), re.IGNORECASE) is not None


def hourly_words(seconds: int | None) -> str:
    """What to tell the person when the hour's allowance is used up."""
    wait = ("up to an hour" if seconds is None or seconds < 1
            else "about " + _plural(-(-seconds // 60), "minute"))
    return ("you have used up this hour's allowance of exact PDFs: CRE Cloud's printer is shared, "
            "so one person may ask for only so many in an hour, all their previews together. "
            f"Wait {wait}, then ask again. The design itself can still be changed and looked at "
            "in the preview meanwhile; only the exact PDF has to wait.")


def age_words(seconds: int) -> str:
    """How long ago something was made, in the largest whole unit that is not too coarse."""
    if seconds >= 2 * 86400:
        return _plural(seconds // 86400, "day")
    if seconds >= 2 * 3600:
        return _plural(seconds // 3600, "hour")
    return _plural(max(1, seconds // 60), "minute")


def _age_of(*answers: dict) -> int | None:
    """How many seconds ago the PDF was made, from the first answer that says."""
    for answer in answers:
        value = answer.get("age_seconds") if isinstance(answer, dict) else None
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            return int(value)
    return None


def patiently(call, say):
    """Make a call; when the engine says it is busy or over its limit (429), wait as long
    as it asks and try again, a bounded number of times. The hour's allowance of exact
    PDFs is the one limit not waited for (HourlyLimit): it asks for more than is worth
    holding a command open, and would only be refused again."""
    waits = 0
    while True:
        try:
            return call()
        except Refused as exc:
            if exc.status != 429:
                raise
            if is_hourly_limit(exc):
                raise HourlyLimit(_asked_seconds(exc.payload)) from None
            if waits >= MAX_WAITS:
                raise Busy(exc.code) from None
            seconds = wait_seconds(exc.payload)
            say(f"the PDF engine is busy, trying again in {seconds} seconds "
                f"(try {waits + 2} of {MAX_WAITS + 1})")
            pause(seconds)
            waits += 1


def _decoded(raw, what: str, signature: bytes, kind: str) -> bytes:
    """Base64 from the site, checked to be the file it says: nothing unchecked is saved."""
    if not isinstance(raw, str) or not raw:
        raise Transport(f"the site could not give back {what}; try again")
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError):
        raise Transport(f"{what} came back damaged (it is not valid {kind} data), so nothing was saved") from None
    if not data.startswith(signature):
        raise Transport(f"{what} is not a {kind} file, so nothing was saved")
    return data


def _write_bytes(path: Path, data: bytes) -> None:
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def cmd_pdf(client: Client, revision: int | None, dpi: int, out_dir: Path | None, with_pdf: bool,
            as_json: bool, folder: Path, fresh: bool = False) -> int:
    """Make a flyer revision's exact PDF, fetch a picture of every page, and say what is on them.

    The pictures are for the assistant to open and look at: the PDF is what CRE Cloud's
    printer makes, so it is what a visitor will download.

    The site keeps the PDF of a revision for ten minutes and answers it again without asking
    CRE Cloud, so a design that has not changed costs nothing to look at twice. A change in
    the design is a new revision and always makes a new PDF; a change in CRE Cloud itself (a
    new attachment, edited property data) does not, which is what `fresh` is for. Either way
    the answer says how old the PDF is, and a PDF over a minute old says so.
    """

    def say(message: str) -> None:
        print(message, file=sys.stderr)

    try:
        made = patiently(lambda: client.flyer_pdf_make(revision, dpi, fresh), say)
        revision = int(made.get("revision", revision or 0))
        include = "both" if with_pdf else "images"
        try:
            stored = patiently(lambda: client.flyer_pdf_get(revision, include), say)
        except Refused as exc:
            if exc.code != "crecs_preview_flyer_pdf_none":
                raise
            print(f"refused: the PDF of revision {revision} was made, but the site no longer holds it, "
                  "so its page pictures cannot be fetched; try again.", file=sys.stderr)
            return 2
    except Busy:
        print(f"refused: the PDF engine stayed busy after {MAX_WAITS + 1} tries. "
              "Wait a minute, then try again.", file=sys.stderr)
        return 2
    except HourlyLimit as limit:
        print("refused: " + hourly_words(limit.seconds), file=sys.stderr)
        return 2

    # Every file is checked before the first is written.
    pictures = {}
    for image in stored.get("images") or []:
        if isinstance(image, dict) and isinstance(image.get("n"), int):
            pictures[image["n"]] = _decoded(image.get("png"), f"the picture of page {image['n']}",
                                           PNG_SIGNATURE, "PNG")
    pdf = _decoded(stored.get("pdf"), "the PDF file itself", PDF_SIGNATURE, "PDF") if with_pdf else None

    host = (urllib.parse.urlparse(client.base).hostname or "site").lower()
    target = (out_dir or folder / "flyer-pages" / host / f"r{revision}").expanduser()
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("page-*.png"):
        if re.fullmatch(r"page-[0-9]+\.png", old.name):
            old.unlink()  # a picture of a page an earlier, longer flyer had
    files = {}
    for n, data in sorted(pictures.items()):
        files[n] = target / f"page-{n}.png"
        _write_bytes(files[n], data)
    pdf_file = None
    if pdf is not None:
        pdf_file = target / f"flyer-r{revision}.pdf"
        _write_bytes(pdf_file, pdf)

    pages = [p for p in (stored.get("pages") or made.get("pages") or []) if isinstance(p, dict) and "n" in p]
    if not pages:
        pages = [{"n": n, "source": "design"} for n in sorted(pictures)]
    warnings = [w for w in (stored.get("warnings") or made.get("warnings") or []) if isinstance(w, dict)]
    count = int(stored.get("page_count") or made.get("page_count") or len(pages))
    resolution = int(stored.get("dpi") or made.get("dpi") or dpi)
    age = _age_of(stored, made)

    if as_json:
        result = {k: v for k, v in stored.items() if k not in ("pdf", "images")}
        if age is not None:
            result["age_seconds"] = age
        result["images"] = [{k: v for k, v in image.items() if k != "png"}
                            for image in stored.get("images") or [] if isinstance(image, dict)]
        result["cached"] = bool(made.get("cached"))
        result["out_dir"] = str(target)
        result["files"] = {"pages": {str(n): str(path) for n, path in files.items()},
                           "pdf": str(pdf_file) if pdf_file else None}
        print(json.dumps(result, indent=1))
        return 0

    size = f", the PDF {round(int(stored['pdf_bytes']) / 1024)} KB" if stored.get("pdf_bytes") else ""
    print(f"The exact PDF of the flyer for {stored.get('property') or made.get('property') or 'the property'} "
          f"is ready: revision {revision}, {_plural(count, 'page')}{size}.")
    if made.get("cached") and fresh:
        # A site whose plugin is older than this skill does not know `fresh` and says nothing
        # about it: the assistant must not take this for the new PDF it asked for.
        print("The site did not make a new PDF as asked: it gave back the one CRE Cloud had already "
              "made (its plugin may be an older version). Do not tell the person this is a new one.")
    elif made.get("cached"):
        print("CRE Cloud had already made this one, so nothing was asked of it again.")
    if age is not None and age > 60:
        print(f"This PDF was made {age_words(age)} ago; ask for a fresh one if something changed in CRE Cloud.")
    print(f"The page pictures, at {resolution} dpi, are saved in {target}:")
    for page in pages:
        n = page["n"]
        where = f"-> {files[n]}" if n in files else "(no picture was made of this page)"
        print(f"  page {n}: {page_words(page)}  {where}")
    if pdf_file:
        print(f"The whole PDF is saved as {pdf_file}")
    if warnings:
        print("Things CRE Cloud noticed:")
        for warning in warnings:
            print(f"  - {warning_words(warning)}")
    else:
        print("CRE Cloud gave no warnings.")
    print("Open every page picture and look at it before telling the person it is right.")
    return 0


# ---------------------------------------------------------------------------------------
# has the flyer been sent, in words
#
# A flyer is sent by a person pressing Send in the preview window (the plugin takes it
# from a signed-in administrator, never from a session's token), so the assistant can only
# ask afterwards. What the answer says is for a person who owns a property website, through
# the assistant: sentences, a time and a page count, no code, no hash.
# ---------------------------------------------------------------------------------------

#: Where a design applies, in words: the choice made when the person pressed Send.
_SEND_SOURCE = {"site": "as the whole site's design", "property": "only for this property"}

_NOT_LIVE_YET = "It is not live yet: visitors keep getting the flyer they got before."

_TIME = re.compile(r"(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::\d{2}(?:\.\d+)?)?(?:Z|\+00:00|\s*UTC)?")


def when_words(value) -> str:
    """A time CRE Cloud gave, written as the preview writes its own (`2026-10-19 12:00 UTC`).
    A time this cannot read is said as it came, and none is said as nothing."""
    text = str(value).strip() if value is not None else ""
    match = _TIME.fullmatch(text)
    return f"{match.group(1)} {match.group(2)} UTC" if match else text


def sent_text(status: dict) -> str:
    """A flyer's status, as the assistant tells it: has it been sent, is CRE Cloud still making
    it, did it fail, is it live, and is it the design on screen."""
    lines = []
    if status.get("property"):
        lines.append(f"Property: {status['property']}.")

    if not status.get("sent"):
        lines.append("Nothing has been sent to CRE Cloud for this property yet, so visitors still get "
                     "the flyer they get today.")
        lines.append("If the person says they pressed Send, it did not go through: ask them to press "
                     "Send again and to tell you what the bar says.")
        return "\n".join(lines)

    state = status.get("state")
    error = status.get("error") if isinstance(status.get("error"), dict) else {}
    reason = str(error.get("message") or "").strip()

    if status.get("retrying"):
        lines.append("CRE Cloud had a problem and is trying again.")
        if reason:
            lines.append(f"It said: {reason}")
        lines.extend([_NOT_LIVE_YET, "Ask again in a little while."])
    elif state in ("queued", "rendering"):
        lines.append("CRE Cloud is still making it.")
        if status.get("requested_at"):
            lines.append(f"It was asked for at {when_words(status['requested_at'])}.")
        lines.extend([_NOT_LIVE_YET, "Ask again in a little while."])
    elif state == "failed":
        lines.append("CRE Cloud could not make the flyer.")
        lines.append(f"It said: {reason}" if reason else "It gave no reason.")
        lines.append("Nothing changed for visitors: the previous flyer, if there was one, keeps being served.")
        lines.append("To try again, the person has to press Send again; if the message is about the "
                     "design, change the design first.")
    elif state == "ready":
        facts = []
        count = status.get("page_count")
        if isinstance(count, int) and not isinstance(count, bool) and count > 0:
            facts.append(_plural(count, "page"))
        if status.get("source") in _SEND_SOURCE:
            facts.append(_SEND_SOURCE[status["source"]])
        made = "CRE Cloud made the flyer"
        if status.get("generated_at"):
            made += f" on {when_words(status['generated_at'])}"
        lines.append(made + (": " + ", ".join(facts) if facts else "") + ".")
        visitors = "Visitors who download this property's flyer get it now."
        if status.get("flyer_url"):
            visitors += f" The link they use: {status['flyer_url']}"
        lines.append(visitors)
    else:
        lines.append(f"CRE Cloud reports a state this command does not know ({state or 'none'}). "
                     "Do not tell the person it is live.")

    # Whether what was sent is what is on screen. A site that does not say is not made to.
    if status.get("up_to_date") is False:
        lines.append("What is on screen in the preview is newer than what was sent: it has changes CRE "
                     "Cloud does not have. To send them, the person has to press Send again; you can "
                     "keep designing first.")
    elif status.get("up_to_date") is True:
        lines.append("What was sent is the design on display in the preview.")

    warnings = [w for w in (status.get("warnings") or []) if isinstance(w, dict)]
    if warnings:
        lines.append("Things CRE Cloud noticed in the last flyer it made:")
        lines.extend(f"  - {warning_words(w)}" for w in warnings)
    elif state == "ready":
        lines.append("CRE Cloud gave no warnings.")
    return "\n".join(lines)


def sent_refusal(exc: Refused) -> str | None:
    """What a refusal to the question means for it, when that is not what any command's refusal
    means: None leaves the usual words."""
    message = str(exc.payload.get("message") or "").strip()
    if exc.status == 502 or exc.code == "crecs_preview_flyer_api":
        said = f" ({message.rstrip('. ')})" if message else ""
        return ("CRE Cloud could not be asked just now, so it is not known whether the flyer was sent"
                f"{said}. Nothing has changed; ask again in a moment.")
    if exc.status == 404 and exc.code == "rest_no_route":
        return ("the site did not understand the question, so it cannot say whether the flyer was sent: its "
                "CRE Cloud Solutions plugin is older than this skill. Ask whoever looks after the site to "
                "update the plugin, and do not tell the person whether the flyer was sent.")
    if exc.status == 404:
        return (f"the site found nothing to answer with: {message or 'not found'} If the preview has ended, "
                f"start a new flyer preview in {ADMIN_SCREEN} and save the box it shows with "
                "`crecs_preview.py connect`.")
    return None


def cmd_sent(client: Client, as_json: bool) -> int:
    """Ask whether the flyer of the property on display has been sent, and how CRE Cloud got on.

    Only ever asks. The person presses Send; this is how the assistant finds out afterwards
    whether it went through, instead of taking the person's word or the button's.
    """
    try:
        status = client.flyer_status()
    except Refused as exc:
        words = sent_refusal(exc)
        if words is None:
            raise
        print(f"refused: {words}", file=sys.stderr)
        return 2
    if not isinstance(status, dict):
        raise Transport("the site's answer about the flyer was not what was expected, so nothing is "
                        "known about it; try again")
    if as_json:
        print(json.dumps({k: v for k, v in status.items() if k != "token"}, indent=1))
    else:
        print(sent_text(status))
    return 0


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


#: What to do about a refusal, for the ones that have an obvious next step.
REFUSAL_HINTS = {
    "crecs_preview_no_property":
        "choose the property to show with `crecs_preview.py property <slug>`, then ask again",
    "crecs_preview_flyer_map_unsupported":
        "nothing was made or sent. Tell the person aerial maps are not available on this site yet, "
        "offer the street map instead, and ask for the PDF again once the design uses it",
}


def _utf8_streams() -> None:
    """Print UTF-8 whatever the pipe's code page.

    Windows gives a piped stdout its ANSI code page, which cannot print what a person
    types into a name (an accent, an emoji), and the assistant reads the pipe as UTF-8.
    """
    for stream in (sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        if encoding != "utf8" and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except (ValueError, OSError):
                pass


def _whole_number(text: str) -> int:
    if not re.fullmatch(r"[0-9]+", text):
        raise argparse.ArgumentTypeError("a revision is a whole number, such as 3")
    return int(text)


def _resolution(text: str) -> int:
    if not re.fullmatch(r"[0-9]+", text) or not 72 <= int(text) <= 150:
        raise argparse.ArgumentTypeError("the page pictures' resolution is a whole number from 72 to 150")
    return int(text)


def main(argv=None) -> int:
    # The shared flags live on a parent parser so they are accepted on either side of
    # the subcommand; argparse otherwise rejects them after it.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--base", help="site base URL, e.g. https://example.com")
    common.add_argument("--session-file", type=Path, help="path to the session file")
    common.add_argument("--insecure", action="store_true", help="skip TLS verification (local .local sites only)")
    common.add_argument("--json", action="store_true", help="print raw JSON")
    # SUPPRESS: a value given before the command is not overwritten by the subcommand's
    # own default, so `--kind flyer state` and `state --kind flyer` both work.
    common.add_argument("--kind", choices=KINDS, default=argparse.SUPPRESS,
                        help="which saved session to use when there is no --session-file: "
                             "property, search or flyer (a command that belongs to one kind needs no --kind)")
    common.add_argument("--session-dir", type=Path, default=argparse.SUPPRESS,
                        help="where session files are kept (default: ~/.crecs)")

    p = argparse.ArgumentParser(description="CRECS preview transport (delivery 4)", parents=[common])
    sub = p.add_subparsers(dest="cmd", required=True)

    for name in ("capabilities", "resume", "state", "undo", "close", "options"):
        sub.add_parser(name, parents=[common])
    sub.add_parser("published", parents=[common],
                   help="a search page session: is the layout on display what the live page shows?")
    sub.add_parser("sent", parents=[common],
                   help="a flyer session: has the flyer been sent to CRE Cloud, and has CRE Cloud made it? "
                        "Only asks: a person sends it, with the Send button in the preview window")

    co = sub.add_parser("connect", parents=[common],
                        help="save the session the Template preview screen shows, after checking it")
    co.add_argument("--from", dest="source", help="a file holding the box's text; default: standard input")

    pd = sub.add_parser("pdf", parents=[common],
                        help="a flyer session: make the exact PDF CRE Cloud prints and save a picture of every page")
    pd.add_argument("--revision", type=_whole_number, help="the revision to make; default: the one on display")
    pd.add_argument("--dpi", type=_resolution, default=96,
                    help="the page pictures' resolution, 72 to 150 (default 96)")
    pd.add_argument("--out-dir", type=Path,
                    help="where to save the pictures; default: a folder for this site and revision under ~/.crecs")
    pd.add_argument("--with-pdf", action="store_true", help="also save the whole PDF file")
    pd.add_argument("--fresh", action="store_true",
                    help="make the PDF again whatever the site has stored, with the property asked for "
                         "anew: for when something changed in CRE Cloud (a new attachment, edited "
                         "property data). A changed design needs no --fresh: it is a new revision")

    cur = sub.add_parser("current", parents=[common])
    cur.add_argument("--out", type=Path, help="write the document here")

    ap = sub.add_parser("apply", parents=[common])
    ap.add_argument("--document", type=Path, required=True, help="JSON file: either an Elementor export or a bare content array")
    ap.add_argument("--base-revision", type=int, help="defaults to the current head")
    ap.add_argument("--key", help="idempotency key; defaults to a random one")

    pr = sub.add_parser("property", parents=[common])
    pr.add_argument("slug")

    me = sub.add_parser("media", parents=[common],
                        help="the site's images, newest first, with the numbers a layout names them by")
    me.add_argument("--search", default="", help="only images whose title has these words")

    ex = sub.add_parser("export", parents=[common])
    ex.add_argument("--out", type=Path, help="write the export here")

    wa = sub.add_parser("watch", parents=[common])
    wa.add_argument("--interval", type=float, default=2.5)

    _utf8_streams()
    args = p.parse_args(argv)
    kind = getattr(args, "kind", None)
    folder = getattr(args, "session_dir", None) or DEFAULT_SESSION_DIR

    if args.cmd == "connect":
        return cmd_connect(args.source, folder, args.insecure, args.json, kind)

    try:
        if args.cmd == "capabilities":
            if not args.base:
                raise Transport("capabilities needs --base")
            # The saved session, when there is one, so the site can say what it tells only someone
            # who may edit templates (the client's logos). Without one, the public answer as always.
            sid, token = capabilities_session(args.base, args.session_file, kind, folder,
                                              announce=lambda message: print(message, file=sys.stderr))
            client = Client(args.base, sid, token, insecure=args.insecure)
            caps = client.capabilities()
            if caps.get("contract") != CONTRACT:
                print(
                    f"warning: site speaks contract {caps.get('contract')}, this client speaks {CONTRACT}",
                    file=sys.stderr,
                )
            if args.json:
                print(json.dumps(caps, indent=1))
            else:
                # flyer_map_types and brand_logos are said in words below, never as a raw value
                # (null included).
                lines = [f"{k:26} {v}" for k, v in caps.items()
                         if not isinstance(v, (dict, list)) and k not in ("flyer_map_types", "brand_logos")]
                kinds = caps.get("session_kinds")
                if isinstance(kinds, list) and kinds:
                    lines.append(f"{'session_kinds':26} " + ", ".join(str(k) for k in kinds))
                if isinstance(caps.get("flyer_pdf"), dict):
                    pdf = caps["flyer_pdf"]
                    lines.append(f"{'flyer_pdf':26} " + ("available" if pdf.get("available") else
                                 "not available: " + str(pdf.get("reason") or "no reason given")))
                if isinstance(caps.get("flyer_send"), dict):
                    send = caps["flyer_send"]
                    lines.append(f"{'flyer_send':26} " + (
                        "available (a person sends it, with the Send button in the preview window)"
                        if send.get("available") else
                        "not available: " + str(send.get("reason") or "no reason given")))
                if "flyer_map_types" in caps:
                    lines.append(f"{'flyer_map_types':26} " + map_types_words(caps["flyer_map_types"]))
                if "brand_logos" in caps:
                    lines.append(f"{'brand_logos':26} " + brand_logos_words(caps["brand_logos"]))
                print("\n".join(lines))
            return 0

        base, sid, token = load_session(
            args.session_file, args.base, kind=kind, natural=NATURAL_KIND.get(args.cmd), folder=folder,
            announce=lambda message: print(message, file=sys.stderr))
        client = Client(base, sid, token, insecure=args.insecure)

        if args.cmd == "watch":
            return cmd_watch(client, args.interval)

        if args.cmd == "pdf":
            return cmd_pdf(client, args.revision, args.dpi, args.out_dir, args.with_pdf, args.json, folder,
                           args.fresh)

        if args.cmd == "sent":
            return cmd_sent(client, args.json)

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
            if not args.json and isinstance(out.get("manifest"), dict) and out["manifest"].get("kind") == "flyer":
                print(flyer_design_text(out, args.out))
                return 0
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
            if out.get("kind") == "search" and "live_hash" in out:
                out["live"] = "yes" if published_answer(out)["live"] else "no"
            if out.get("kind") == "flyer" and not args.json:
                print(flyer_state_text(out))
                return 0
        elif args.cmd == "published":
            out = published_answer(client.state())
            if not args.json:
                print(out["say"])
                return 0
        elif args.cmd == "resume":
            out = client.resume()
        elif args.cmd == "undo":
            out = client.undo()
        elif args.cmd == "close":
            out = client.close()
        elif args.cmd == "options":
            out = client.search_options()
            if not args.json:
                # Every name in full, one a line: these are what a layout must spell.
                for key, label in (("property_types", "property types"), ("brokers", "brokers")):
                    names = out.get(key) or []
                    print(f"{label} ({len(names)}):")
                    for name in names:
                        print(f"  {name}")
                return 0
        elif args.cmd == "media":
            out = client.media(args.search)
            if not args.json:
                # The number first: it is what a layout's pin_image takes.
                images = out.get("images") or []
                print(f"images ({len(images)}), newest first:")
                for img in images:
                    size = f"{img.get('width')}x{img.get('height')}" if img.get("width") else "size unknown"
                    print(f"  {str(img.get('id')):>7}  {img.get('title') or '(no title)'}  [{img.get('file')}, {size}, "
                          f"uploaded {str(img.get('uploaded', ''))[:10]}]")
                return 0
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
        if exc.code in REFUSAL_HINTS:
            print(f"  {REFUSAL_HINTS[exc.code]}", file=sys.stderr)
        for finding in (exc.payload.get("findings") or [])[:8]:
            # CRE Cloud's own findings about a flyer's printing carry no level: they are all
            # reasons the PDF was not made.
            if isinstance(finding, dict) and finding.get("level", "error") == "error":
                # A property template's findings name an element; a search layout's or a
                # flyer's, a block; CRE Cloud's, the part of the markup.
                where = (finding.get("element") or finding.get("node")
                         or (finding.get("where") or {}).get("part") or "the flyer")
                print(f"  [{finding.get('code')}] {where}: {finding.get('message')}", file=sys.stderr)
        return 2
    except Transport as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
