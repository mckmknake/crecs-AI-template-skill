"""The workspace: where the working document, its revision history and the decision
log live — outside the chat, and separate from the importable JSON.

Three properties matter:

* **atomic writes.** Every file is written to a temporary sibling and moved into
  place, so an interrupted run never leaves a half-written document.
* **base-revision check.** Each commit verifies that ``document.json`` still hashes
  to what the last commit recorded. If someone edited it in another tool, the commit
  is refused rather than silently overwriting their work.
* **resumable.** ``state.json`` carries everything another session needs, so work can
  continue in a different conversation or a different harness.
"""

import datetime
import hashlib
import json
import os
import shutil

from .catalog import Catalog
from .document import Document, DocumentError

STATE_FILE = "state.json"
DOCUMENT_FILE = "document.json"
DECISIONS_FILE = "decisions.md"
HISTORY_DIR = "history"
BASE_COPY = "base-template.json"

STATE_VERSION = 1


class StateError(Exception):
    pass


def _now():
    return datetime.datetime.now(datetime.timezone.utc).replace(
        microsecond=0
    ).isoformat()


def canonical_bytes(payload):
    """Stable serialisation used for hashing, so formatting never shifts a hash."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sha256_of(payload):
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def write_json_atomic(path, payload, indent=2):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=indent, ensure_ascii=False)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def write_text_atomic(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def read_json(path, what="file"):
    if not os.path.isfile(path):
        raise StateError("%s not found: %s" % (what, path))
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    try:
        return json.loads(text)
    except ValueError as exc:
        raise StateError(_not_json_message(path, what, text, exc))


def _not_json_message(path, what, text, exc):
    """Say what the file actually is, not just that json.loads was unhappy.

    A template export fetched from a site whose login has expired comes back as the
    WordPress login page. "Expecting value: line 1 column 1" sends someone hunting for a
    corrupt file; naming the HTML sends them to sign in again.
    """
    head = text.lstrip()[:400].lower()
    if head.startswith("<!doctype") or head.startswith("<html") or "<body" in head:
        hint = ""
        if "loginform" in head or "wp-login" in head or "user_login" in head:
            hint = (" It looks like the WordPress login page, which is what a template "
                    "export returns once the session has expired — sign in to the site "
                    "again and export the template afresh.")
        return ("%s is an HTML page, not JSON: %s.%s" % (what, path, hint))
    return "%s is not valid JSON (%s): %s" % (what, path, exc)


#: Elementor export types this tool can edit. Anything else came from the same screen
#: but is a different kind of thing.
_EDITABLE_TEMPLATE_TYPES = ("page", "section", "container", "wp-page", "")


def _reject_obvious_non_template(path, payload):
    """Catch the near misses before the generic parser produces a vaguer complaint."""
    if not isinstance(payload, dict):
        return  # a bare element array is fine; Document will judge it

    if "code" in payload and "message" in payload:
        raise StateError(
            "%s is a WordPress error response, not a template: %s — %s\nExport the "
            "template again once that is resolved."
            % (path, payload.get("code"), payload.get("message"))
        )

    if "content" not in payload:
        raise StateError(
            "%s is JSON but not an Elementor export: it has no \"content\" key "
            "(found %s). In WordPress, use Templates -> Saved Templates -> Export on "
            "the property page template, and pass the file it downloads."
            % (path, ", ".join(sorted(payload)[:6]) or "nothing")
        )

    kind = payload.get("type")
    if isinstance(kind, str) and kind not in _EDITABLE_TEMPLATE_TYPES:
        raise StateError(
            "%s is an Elementor export of type %r, which this tool does not edit. "
            "Export the property page template itself, not the %s."
            % (path, kind, kind)
        )


def baseline_keys_of(document):
    """Every ``elementId::settingKey`` present right now.

    Recorded at import so the validator can tell a pre-existing unknown key — which
    must be preserved and merely flagged — from one introduced later, which has no
    confirmed contract and is blocked.
    """
    keys = set()
    for element in document.elements():
        try:
            settings = element.settings
        except DocumentError:
            continue
        for key in settings:
            keys.add("%s::%s" % (element.id, key))
    return keys


class Workspace:
    def __init__(self, path, state):
        self.path = path
        self.state = state

    # -- paths ---------------------------------------------------------------

    def _p(self, *parts):
        return os.path.join(self.path, *parts)

    @property
    def document_path(self):
        return self._p(DOCUMENT_FILE)

    @property
    def state_path(self):
        return self._p(STATE_FILE)

    @property
    def decisions_path(self):
        return self._p(DECISIONS_FILE)

    # -- lifecycle -----------------------------------------------------------

    @classmethod
    def init(cls, path, base_template, profile_path=None, force=False, catalog=None):
        if os.path.exists(path) and os.listdir(path):
            if not force:
                raise StateError(
                    "%s already exists and is not empty. Use --force to start over "
                    "(this discards the current working document and its history)."
                    % path
                )
            shutil.rmtree(path)
        os.makedirs(cls._history_path(path), exist_ok=True)

        payload = read_json(base_template, "base template")
        _reject_obvious_non_template(base_template, payload)
        try:
            document = Document(payload)
        except DocumentError as exc:
            raise StateError("base template %s is not a usable Elementor export: %s"
                             % (base_template, exc))

        catalog = catalog or Catalog.load_default()
        document_sha = sha256_of(document.to_envelope())

        state = {
            "state_version": STATE_VERSION,
            "created_at": _now(),
            "updated_at": _now(),
            "workdir": os.path.abspath(path),
            "base_template": os.path.abspath(base_template),
            "base_sha256": sha256_of(payload),
            "document_sha256": document_sha,
            "revision": 0,
            "profile_path": os.path.abspath(profile_path) if profile_path else None,
            "catalog": catalog.fingerprint(),
            "baseline_keys": sorted(baseline_keys_of(document)),
            "history": [],
        }

        workspace = cls(os.path.abspath(path), state)
        write_json_atomic(workspace.document_path, document.to_envelope())
        write_json_atomic(workspace._p(BASE_COPY), payload)
        write_json_atomic(workspace.state_path, state)
        write_text_atomic(
            workspace.decisions_path,
            "# Decisions\n\n"
            "Why this template looks the way it does. Written by the tool; append "
            "freely by hand.\n\n"
            "- %s — workspace created from `%s` (revision 0)\n"
            % (state["created_at"], os.path.basename(base_template))
        )
        return workspace

    @staticmethod
    def _history_path(path):
        return os.path.join(path, HISTORY_DIR)

    @classmethod
    def open(cls, path):
        state_path = os.path.join(path, STATE_FILE)
        if not os.path.isfile(state_path):
            raise StateError(
                "no workspace at %s. Create one first:\n"
                "  crecs_template.py init --from <template.json> --workdir %s"
                % (path, path)
            )
        state = read_json(state_path, "workspace state")
        if state.get("state_version") != STATE_VERSION:
            raise StateError(
                "workspace at %s was written by a different tool version "
                "(state_version=%r, this build expects %r)."
                % (path, state.get("state_version"), STATE_VERSION)
            )
        return cls(os.path.abspath(path), state)

    # -- document ------------------------------------------------------------

    def load_document(self, accept_external=False):
        payload = read_json(self.document_path, "working document")
        actual = sha256_of(payload)
        if actual != self.state.get("document_sha256") and not accept_external:
            self._external = True
        document = Document(payload)
        return document

    def external_change_pending(self):
        payload = read_json(self.document_path, "working document")
        return sha256_of(payload) != self.state.get("document_sha256")

    def commit(self, document, summary, decision=None, op="edit",
               accept_external=False):
        if self.external_change_pending() and not accept_external:
            raise StateError(
                "%s changed outside this tool since revision %s, so committing would "
                "discard that edit. Re-run with --accept-external to take the file as "
                "it is now, or restore it from %s/."
                % (DOCUMENT_FILE, self.state.get("revision"), HISTORY_DIR)
            )

        previous = read_json(self.document_path, "working document")
        revision = int(self.state.get("revision", 0)) + 1

        snapshot = os.path.join(
            self._history_path(self.path), "%04d-before-%s.json" % (revision, op)
        )
        write_json_atomic(snapshot, previous)

        envelope = document.to_envelope()
        write_json_atomic(self.document_path, envelope)

        self.state["revision"] = revision
        self.state["document_sha256"] = sha256_of(envelope)
        self.state["updated_at"] = _now()
        self.state.setdefault("history", []).append({
            "revision": revision,
            "at": self.state["updated_at"],
            "op": op,
            "summary": summary,
            "snapshot": os.path.relpath(snapshot, self.path).replace("\\", "/"),
            "decision": decision,
        })
        write_json_atomic(self.state_path, self.state)

        if decision:
            with open(self.decisions_path, "a", encoding="utf-8", newline="\n") as fh:
                fh.write("- %s — r%d %s: %s\n"
                         % (self.state["updated_at"], revision, summary, decision))
        return revision

    # -- history -------------------------------------------------------------

    def history(self):
        return list(self.state.get("history", []))

    def undo(self, steps=1):
        if steps < 1:
            raise StateError("--steps must be 1 or more")
        entries = [h for h in self.history() if h.get("snapshot")]
        if not entries:
            raise StateError(
                "nothing to undo: the workspace is still at revision 0."
            )
        if steps > len(entries):
            raise StateError(
                "cannot undo %d steps; only %d recorded revisions are available."
                % (steps, len(entries))
            )
        target = entries[-steps]
        snapshot_path = os.path.join(self.path, target["snapshot"])
        payload = read_json(snapshot_path, "history snapshot")
        document = Document(payload)
        return self.commit(
            document,
            "undo %d step(s), back to the content before r%s"
            % (steps, target["revision"]),
            op="undo",
            accept_external=True,
        )

    # -- misc ----------------------------------------------------------------

    def baseline_keys(self):
        return set(self.state.get("baseline_keys") or [])

    def decisions_text(self):
        if not os.path.isfile(self.decisions_path):
            return ""
        with open(self.decisions_path, encoding="utf-8") as fh:
            return fh.read()

    def resume_summary(self):
        return {
            "workdir": self.path,
            "revision": self.state.get("revision"),
            "document_sha256": self.state.get("document_sha256"),
            "base_template": self.state.get("base_template"),
            "profile_path": self.state.get("profile_path"),
            "catalog": self.state.get("catalog"),
            "updated_at": self.state.get("updated_at"),
            "history_entries": len(self.history()),
            "document": self.document_path,
            "decisions": self.decisions_path,
        }
