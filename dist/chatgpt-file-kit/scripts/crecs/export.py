"""Export.

The working document and the export are different files on purpose. The export is
plain Elementor JSON — no Markdown, no comments, no bookkeeping keys — and it is
refused while an ERROR stands. A draft can still be written, but it is named as
incomplete both on stdout and in a sidecar report.

The destination may be ``-``, meaning the stream instead of a file. That exists for
surfaces with no writable project directory, where an export onto a path has nowhere
to go. In that mode the stream carries the envelope and nothing else — no summary, no
sidecar — because anything else on it stops the output being a file.
"""

import copy
import json
import os
import sys

from .document import Document
from .state import write_json_atomic

ENVELOPE_ORDER = ("content", "page_settings", "version", "title", "type")
INTERNAL_PREFIXES = ("_crecs", "crecs_studio_")

#: ``--out`` value meaning "write to the stream, not to a file".
STDOUT_PATH = "-"


class ExportError(Exception):
    pass


def build_envelope(document, title=None):
    """Normalise to the five-key Elementor envelope, dropping nothing else."""
    payload = document.to_envelope()
    if isinstance(payload, list):
        envelope = {
            "content": payload,
            "page_settings": [],
            "version": "0.4",
            "title": title or "Property Page",
            "type": "page",
        }
    else:
        envelope = copy.deepcopy(payload)
        envelope.setdefault("page_settings", [])
        envelope.setdefault("version", "0.4")
        envelope.setdefault("type", "page")
        if title:
            envelope["title"] = title
        envelope.setdefault("title", "Property Page")

    for key in list(envelope):
        if key not in ENVELOPE_ORDER:
            # Anything else is bookkeeping that Elementor does not read.
            del envelope[key]

    ordered = {}
    for key in ENVELOPE_ORDER:
        ordered[key] = envelope[key]
    return ordered


def _strip_internal(node):
    """Remove keys this tool could have added. It never adds any, so this is a guard
    against a hand-edited working file leaking bookkeeping into an import."""
    removed = []
    if isinstance(node, dict):
        for key in list(node):
            if any(key.startswith(p) for p in INTERNAL_PREFIXES):
                del node[key]
                removed.append(key)
            else:
                removed.extend(_strip_internal(node[key]))
    elif isinstance(node, list):
        for item in node:
            removed.extend(_strip_internal(item))
    return removed


def export(workspace, out_path, catalog, profile, allow_draft=False, title=None,
           accept_external=False, stream=None):
    """Validate, then write the export plus a sidecar report.

    ``out_path`` of ``-`` writes the envelope to ``stream`` (stdout by default) and
    writes no sidecar, because there is no path to put one beside.

    Returns (report, written_path or None).
    """
    from . import validate as validate_mod

    payload = json.load(open(workspace.document_path, encoding="utf-8"))
    document = Document(copy.deepcopy(payload))

    applied = profile.apply(document)
    result = validate_mod.validate(document, catalog, profile,
                                   baseline_keys=workspace.baseline_keys())

    envelope = build_envelope(document, title=title)
    stripped = _strip_internal(envelope)

    report = {
        "generated_by": "crecs-property-template export",
        "workdir": workspace.path,
        "source_revision": workspace.state.get("revision"),
        "source_document_sha256": workspace.state.get("document_sha256"),
        "catalog": catalog.fingerprint(),
        "profile": profile.describe() if not profile.is_empty() else None,
        "applied_profile_mappings": applied,
        "internal_keys_stripped": stripped,
        "counts": result.counts,
        "ready": result.is_exportable,
        "claim_level": (
            "static validation passed; not imported into Elementor and not rendered"
            if result.is_exportable
            else "draft: static validation found blocking errors"
        ),
        "findings": [f.to_dict() for f in result.findings],
    }

    if not result.is_exportable and not allow_draft:
        return report, None

    report["draft"] = not result.is_exportable

    if out_path == STDOUT_PATH:
        # Nothing but the envelope goes on this stream, and no sidecar is written:
        # there is no path to put one beside. The report still comes back to the
        # caller, which prints its summary to stderr.
        target = sys.stdout if stream is None else stream
        data = json.dumps(envelope, indent=2, ensure_ascii=False) + "\n"
        # Go through the binary buffer when there is one. A real stdout encodes with
        # the console codepage — cp1252 on Windows — which mangles any character the
        # template happens to carry, and a redirect then produces a file that is not
        # valid UTF-8. The file export does not have this problem because it opens
        # with an explicit encoding; this makes the two agree byte for byte.
        buffer = getattr(target, "buffer", None)
        if buffer is not None:
            buffer.write(data.encode("utf-8"))
            buffer.flush()
        else:
            target.write(data)
        report["export_path"] = STDOUT_PATH
        report["export_stream"] = True
        return report, STDOUT_PATH

    write_json_atomic(out_path, envelope)
    report["export_path"] = os.path.abspath(out_path)
    report["export_stream"] = False
    write_json_atomic(out_path + ".report.json", report)
    return report, out_path
