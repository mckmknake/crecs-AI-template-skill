"""crecs_flyer.py — edit the property flyer's layout document.

The flyer's designed pages are drawn by the plugin from a layout document
(references/flyer/FLYER-LAYOUT.md). This edits one, as a local file:

    crecs_flyer.py --file flyer.json new --from landscape-classic
    crecs_flyer.py --file flyer.json show
    crecs_flyer.py --file flyer.json set --node <id> --key name_color --value "#0a3d62"
    crecs_flyer.py --file flyer.json add --type photo --into <column id>
    crecs_flyer.py --file flyer.json validate

Every change is checked against the plugin's vocabulary before it is written, and a
change that would make the plugin refuse the flyer is not written at all, so the file is
always one the preview accepts. Nothing here talks to the site: crecs_preview.py does.
Nothing here sends a flyer: a person does, from the preview.

Exit codes: 0 done, 1 refused (the flyer would break), 2 bad request (unknown block,
setting or value), 3 file problem.
"""

import argparse
import copy
import difflib
import json
import os
import re
import sys
import tempfile

from . import __version__
from .flyer_layout import (SIDES, FlyerLayoutError, Vocabulary, blocking, find,
                           new_id, normalise, php_list, settings_of, walk)

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_FILE = 3

FILE_ENV = "CRECS_FLYER_FILE"
DEFAULT_FILE = "flyer-layout.json"

ROW, COLUMN, LOGO = "crecs_flyer_row", "crecs_flyer_column", "crecs_flyer_logo"

# Suffixes other layouts use for a state or a device. A flyer is printed: it has neither.
_NOT_PRINTED = re.compile(r"_(?:hover|desktop|tablet|mobile)$")


class Refused(Exception):
    """The change would make the plugin refuse the flyer."""

    def __init__(self, message, findings):
        super().__init__(message)
        self.findings = findings


class Usage(Exception):
    """The request names something that does not exist, or a value that cannot be."""


# Findings whose words carry a count. A smaller count is the same problem, shrinking: a
# design already refused can be mended a step at a time without each step being refused.
# Each message below is worded so that every number in it shrinks, or stays, as the
# design gets better: a row's widths and its columns and gaps against the narrowest page,
# a fixed height's padding and border and how many px it is short, and the px a page's
# bands and padding take.
_NUMBERS = re.compile(r"[0-9]+")
_COUNTED = ("E-FL-LIMIT", "E-FL-PAGES", "E-FL-ONCE")
_COUNTED_VALUES = (
    re.compile(r"^The columns of this row"),
    re.compile(r"^The [0-9]+ columns of this row, at least [0-9]+ px each"),
    re.compile(r"^crecs_flyer_[a-z_]+ \"[a-z_]+\" leaves less than [0-9]+ px for what the block holds"),
    re.compile(r"^The flyer's padding and border, the header and footer heights"),
)


def _counted(finding):
    message = finding.get("message") or ""
    return finding.get("code") in _COUNTED or (
        finding.get("code") == "E-FL-VALUE" and any(p.match(message) for p in _COUNTED_VALUES))


def _known(finding, before):
    """Was this problem already there? The same finding, or one that only counts less."""
    if finding in before:
        return True
    if not _counted(finding):
        return False
    message = finding.get("message") or ""
    shape, numbers = _NUMBERS.sub("#", message), [int(n) for n in _NUMBERS.findall(message)]
    for old in before:
        old_message = old.get("message") or ""
        old_numbers = [int(n) for n in _NUMBERS.findall(old_message)]
        if old.get("code") == finding.get("code") and old.get("node") == finding.get("node") \
                and _NUMBERS.sub("#", old_message) == shape and len(old_numbers) == len(numbers) \
                and all(n <= o for n, o in zip(numbers, old_numbers)):
            return True
    return False


# ---------------------------------------------------------------------------
# file
# ---------------------------------------------------------------------------


def default_file():
    return os.environ.get(FILE_ENV) or DEFAULT_FILE


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            document = json.load(fh)
    except FileNotFoundError:
        raise FlyerLayoutError(
            "%s does not exist. Start one from a built-in design: crecs_flyer.py --file %s new "
            "--from <design>, or fetch the flyer the preview shows: crecs_preview.py "
            "--session-file <file> current --out %s" % (path, path, path))
    except (OSError, ValueError) as exc:
        raise FlyerLayoutError("%s could not be read: %s" % (path, exc))
    if isinstance(document, dict) and "document" in document and "manifest" in document:
        document = document["document"]  # a saved export payload
    kind = document.get("type") if isinstance(document, dict) else None
    if kind == "crecs-search-layout":
        raise FlyerLayoutError("%s is the search page's layout, not a flyer: use crecs_search.py." % path)
    if kind != "crecs-flyer-layout":
        raise FlyerLayoutError(
            "%s is not a flyer layout. If it came from a property page preview, this is the "
            "wrong tool: use crecs_template.py." % path)
    return normalise(document)


def save(path, document):
    normalise(document)
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(prefix=".crecs-flyer-", suffix=".json", dir=folder)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(document, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        os.replace(temp, path)
    except BaseException:
        if os.path.exists(temp):
            os.unlink(temp)
        raise


# ---------------------------------------------------------------------------
# values
# ---------------------------------------------------------------------------

_LENGTH = re.compile(r"^(-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+))([a-z%]*)$")


def _number(text):
    return int(text) if re.match(r"^-?[0-9]+$", text) else float(text)


def _default_unit(spec):
    units = spec.get("units", [])
    if "" in units:
        return ""
    return "px" if "px" in units else (units[0] if units else "")


def _length(token):
    match = _LENGTH.match(token.strip())
    if not match:
        raise Usage("%r is not a length, such as 24px or 50%%" % token)
    return _number(match.group(1)), match.group(2)


def parse_value(spec, raw):
    """A command-line value in the shape the control stores.

    JSON is taken as it is. Otherwise the familiar shorthand for the control's type:
    `24px` or `1.4` for a size, `8px 16px` for four sides as in CSS, `320` or `320px` for a
    number of pixels, `auto` where a number may be automatic, and `total_sf, rates` for a
    choice of parts.
    """
    kind = spec["type"]
    try:
        parsed = json.loads(raw)
    except ValueError:
        parsed = raw

    if kind in ("color", "select", "font", "text"):
        return parsed if isinstance(parsed, str) else raw
    if kind == "number":
        if isinstance(parsed, int) and not isinstance(parsed, bool):
            return parsed
        text = str(parsed).strip() if not isinstance(parsed, bool) else ""
        if spec.get("auto") and text.lower() == "auto":
            return "auto"
        unit = spec.get("unit")
        if unit and text.endswith(unit):
            text = text[:-len(unit)].strip()
        if re.match(r"^-?[0-9]+$", text):
            return int(text)
        raise Usage("must be a whole number%s%s" % (
            {"px": " of pixels", "%": " (a percentage)"}.get(unit, ""),
            ', or "auto"' if spec.get("auto") else ""))
    if kind == "media":
        if isinstance(parsed, int) and not isinstance(parsed, bool):
            return parsed
        raise Usage("must be an image's number, such as 6543: `crecs_preview.py media` lists them")
    if kind == "fields":
        if parsed is None or isinstance(parsed, list):
            return parsed
        if parsed is raw:  # not JSON: parts separated by commas
            names = [name.strip() for name in raw.split(",")]
        elif isinstance(parsed, str):
            names = [parsed]
        else:
            raise Usage('give the parts as a JSON list, ["total_sf", "rates"], or separated by commas')
        return [name for name in names if name] or None
    if kind == "slider":
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, (int, float)) and not isinstance(parsed, bool):
            return {"unit": _default_unit(spec), "size": parsed}
        size, unit = _length(str(parsed))
        return {"unit": unit if unit or "" in spec["units"] else _default_unit(spec), "size": size}
    if kind == "dimensions":
        if isinstance(parsed, dict):
            return parsed
        tokens = str(parsed).split()
        if not 1 <= len(tokens) <= 4:
            raise Usage("give one to four lengths, as in CSS: 8px, 8px 16px, or 1px 2px 3px 4px")
        lengths = [_length(t) for t in tokens]
        units = {u for n, u in lengths if u or n != 0}
        if len(units) > 1:
            raise Usage("all four sides need the same unit")
        unit = (units.pop() if units else "") or _default_unit(spec)
        n = [v for v, _u in lengths]
        if len(n) == 1:
            top = right = bottom = left = n[0]
        elif len(n) == 2:
            top, right, bottom, left = n[0], n[1], n[0], n[1]
        elif len(n) == 3:
            top, right, bottom, left = n[0], n[1], n[2], n[1]
        else:
            top, right, bottom, left = n
        return {"unit": unit, "top": top, "right": right, "bottom": bottom, "left": left,
                "isLinked": top == right == bottom == left}
    return parsed


def show_value(value):
    if isinstance(value, dict) and "size" in value and "unit" in value and len(value) <= 3:
        return "%s%s" % (value["size"], value["unit"])
    if isinstance(value, dict) and all(side in value for side in SIDES):
        return " ".join("%s%s" % (value[s], value.get("unit", "")) for s in SIDES)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def page_words(vocab, orientation):
    box = vocab.page_boxes.get(orientation) or ["?", "?"]
    return "%s x %s pixels (US Letter %s)" % (box[0], box[1], orientation)


# ---------------------------------------------------------------------------
# operations
# ---------------------------------------------------------------------------


class Editor:
    def __init__(self, vocab, document):
        self.vocab = vocab
        self.document = document

    # -- lookup --------------------------------------------------------------

    def node(self, node_id):
        try:
            return find(self.document, node_id)
        except FlyerLayoutError as exc:
            raise Usage(str(exc))

    def describe(self, node):
        return "%s (%s)" % (self.vocab.label(node.get("widgetType")), node.get("id"))

    def control_name(self, node, key):
        controls = self.vocab.controls(node.get("widgetType"))
        if key in controls:
            return key, controls[key]
        if _NOT_PRINTED.search(key):
            raise Usage("%s has no %s setting. A flyer is printed: there is no hover state and no "
                        "device, so each setting has one value. List them with: controls --node %s"
                        % (self.describe(node), key, node.get("id")))
        close = difflib.get_close_matches(key, list(controls), n=4, cutoff=0.6)
        hint = " Did you mean: %s?" % ", ".join(close) if close else \
            " List them with: controls --node %s" % node.get("id")
        raise Usage("%s has no %s setting.%s" % (self.describe(node), key, hint))

    def columns(self, row):
        return [c for c in php_list(row.get("elements")) or []
                if isinstance(c, dict) and c.get("widgetType") == COLUMN]

    def root(self):
        content = self.document.get("content")
        first = content[0] if isinstance(content, list) and content else None
        if not isinstance(first, dict) or first.get("widgetType") != self.vocab.root:
            raise Usage("this flyer has no %s block at its root" % self.vocab.root)
        return first

    # -- checks --------------------------------------------------------------

    def commit(self, before, what):
        """Refuse the change if it brings a problem the document did not have.

        A problem the document already had is no new one, and neither is the same problem
        counting less (fewer pages, fewer blocks, a row less over its width), so a flyer
        that is already refused can be mended a step at a time.
        """
        after = self.vocab.check(self.document)
        new = [f for f in after if f.get("level") == "error" and not _known(f, before)]
        if new:
            raise Refused(what, new)
        return after

    # -- settings ------------------------------------------------------------

    def set(self, node_id, key, raw):
        node, *_ = self.node(node_id)
        block_type = node.get("widgetType")
        if block_type == ROW and key == "widths":
            return self._set_widths(node, raw)
        name, spec = self.control_name(node, key)
        try:
            value = parse_value(spec, raw)
        except Usage as exc:
            raise Usage("%s: %s %s" % (self.describe(node), name, exc))
        if value is None or self.vocab.is_unset(spec, value):
            return self.unset(node_id, name)
        problem = self.vocab.problem(spec, value)
        if problem is not None:
            raise Usage("%s: %s %s" % (self.describe(node), name, problem))
        settings = settings_of(node)
        message = "%s: %s is now %s." % (self.describe(node), name, json.dumps(value, ensure_ascii=False))
        if block_type == LOGO:
            message = self._logo_companions(node, settings, name, value) or message
        settings[name] = value
        return {"node": node["id"], "block": self.vocab.label(block_type), "setting": name,
                "value": value, "message": message}

    def _logo_companions(self, node, settings, name, value):
        """A logo's image and its source change together: one alone is always refused."""
        if name == "media_id":
            settings["source"] = "media"
            return "%s: shows the media library image %s (source media, media_id %s)." % (
                self.describe(node), value, value)
        if name == "source" and value != "media":
            settings.pop("media_id", None)
            return "%s: shows the site's own logo." % self.describe(node)
        if name == "source" and self.vocab.option(node, "media_id") is None:
            raise Usage("%s: give the image instead, and the source changes with it: set --node %s "
                        "--key media_id --value <number> (crecs_preview.py media lists the images)"
                        % (self.describe(node), node.get("id")))
        return None

    def _set_widths(self, row, raw):
        """Every column's width at once, in order: one at a time a row often overflows."""
        columns = self.columns(row)
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = raw
        parts = parsed if isinstance(parsed, list) else str(parsed).split(",")
        if len(parts) != len(columns):
            raise Usage("%s has %d columns: give one width for each, in order, such as 60, 40 "
                        "(auto leaves a column to share what the others leave)"
                        % (self.describe(row), len(columns)))
        spec = self.vocab.controls(COLUMN)["width"]
        widths = []
        for column, part in zip(columns, parts):
            text = "" if part is None else str(part).strip()
            if text.lower() in ("", "auto"):
                widths.append(None)
                continue
            try:
                value = parse_value(spec, text)
            except Usage as exc:
                raise Usage("%s: width %s" % (self.describe(column), exc))
            problem = self.vocab.problem(spec, value)
            if problem is not None:
                raise Usage("%s: width %s" % (self.describe(column), problem))
            widths.append(value)
        for column, width in zip(columns, widths):
            settings = settings_of(column)
            if width is None:
                settings.pop("width", None)
            else:
                settings["width"] = width
        words = ", ".join("auto" if w is None else "%d%%" % w for w in widths)
        return {"node": row["id"], "block": self.vocab.label(ROW), "setting": "widths",
                "value": widths, "message": "%s: its columns are now %s wide." % (self.describe(row), words)}

    def unset(self, node_id, key):
        node, *_ = self.node(node_id)
        block_type = node.get("widgetType")
        settings = settings_of(node)
        if block_type == ROW and key == "widths":
            had = False
            for column in self.columns(node):
                had = settings_of(column).pop("width", None) is not None or had
            return {"node": node["id"], "block": self.vocab.label(ROW), "setting": "widths",
                    "removed": had, "message": "%s: its columns share it evenly." % self.describe(node)}
        name, _spec = self.control_name(node, key)
        had = name in settings
        settings.pop(name, None)
        if block_type == LOGO and (name == "source" or (name == "media_id" and settings.get("source") == "media")):
            settings.pop("source", None)
            settings.pop("media_id", None)
        message = ("%s: %s removed; the block's own value applies." if had else
                   "%s: %s was not set.") % (self.describe(node), name)
        return {"node": node["id"], "block": self.vocab.label(block_type), "setting": name,
                "removed": had, "message": message}

    def text(self, node_id, slot, value=None, reset=False):
        node, *_ = self.node(node_id)
        texts = (self.vocab.block(node.get("widgetType")) or {}).get("texts") or {}
        if slot not in texts:
            have = ", ".join(texts) if texts else "none"
            raise Usage("%s has no %s text (its texts: %s)" % (self.describe(node), slot, have))
        if reset:
            return self.unset(node_id, "text_" + slot)
        # A line break is written \n on the command line; a one-line text refuses it.
        return self.set(node_id, "text_" + slot, json.dumps(value.replace("\\n", "\n"), ensure_ascii=False))

    def orientation(self, value):
        root = self.root()
        spec = self.vocab.controls(self.vocab.root)["orientation"]
        problem = self.vocab.problem(spec, value)
        if problem is not None or value in ("", None):
            raise Usage("the orientation %s" % (problem or "must be one of: " + ", ".join(
                '"%s"' % o for o in spec["options"])))
        settings_of(root)["orientation"] = value
        return {"node": root["id"], "orientation": value, "page": self.vocab.page_boxes.get(value),
                "message": "The flyer's designed pages are now %s: %s." % (value, page_words(self.vocab, value))}

    # -- structure -----------------------------------------------------------

    def _place(self, into=None, position=None, before=None, after=None):
        """(list, index) where a block goes."""
        if into is not None:
            parent, *_ = self.node(into)
            block = self.vocab.block(parent.get("widgetType"))
            if not block or block["kind"] != "container":
                raise Usage("%s cannot hold other blocks" % self.describe(parent))
            if not isinstance(parent.get("elements"), list):
                parent["elements"] = []
            elements = parent["elements"]
            index = len(elements) if position is None else max(0, min(int(position), len(elements)))
            return elements, index
        anchor_id = before if before is not None else after
        if anchor_id is None:
            raise Usage("say where: --into <block>, --before <block> or --after <block>")
        _anchor, parent_list, index, _ancestors = self.node(anchor_id)
        return parent_list, index + (1 if after is not None else 0)

    def _where(self, node_id):
        _node, _list, index, ancestors = find(self.document, node_id)
        parent = ancestors[-1] if ancestors else None
        return ("into %s, position %d" % (self.describe(parent), index + 1)) if parent else "at the top"

    def move(self, node_id, into=None, position=None, before=None, after=None):
        node, parent_list, index, _ancestors = self.node(node_id)
        if node.get("widgetType") == self.vocab.root:
            raise Usage("the Flyer block is the root; everything else moves inside it")
        target_id = into if into is not None else (before if before is not None else after)
        if target_id is not None:
            _t, _tl, _ti, target_ancestors = self.node(target_id)
            if target_id == node_id or any(a is node for a in target_ancestors):
                raise Usage("a block cannot go inside itself")
        parent_list.pop(index)
        try:
            elements, at = self._place(into, position, before, after)
        except Usage:
            parent_list.insert(index, node)
            raise
        elements.insert(at, node)
        return {"node": node_id, "block": self.vocab.label(node.get("widgetType")), "moved": True,
                "message": "%s moved %s." % (self.describe(node), self._where(node_id))}

    def add(self, type_name, into=None, position=None, before=None, after=None, node_id=None, columns=0):
        block_type = self.vocab.resolve(type_name)
        if block_type is None:
            raise Usage("there is no %s block in a flyer; `crecs_flyer.py blocks` lists them" % type_name)
        if block_type == self.vocab.root:
            raise Usage("a flyer has one Flyer block, its root: to start another flyer, use new --from <design>")
        block = self.vocab.block(block_type)
        if node_id is not None:
            if not self.vocab.is_id(node_id):
                raise Usage("a block id is 4 to 16 letters or digits")
            if any(n.get("id") == node_id for n, *_ in walk(self.document)):
                raise Usage("the id %s is taken by another block" % node_id)
        if columns and block_type != ROW:
            raise Usage("--columns is for a row")
        if into is None and before is None and after is None:
            parents = [n for n, *_ in walk(self.document) if n.get("widgetType") in (block["within"] or [])]
            if len(parents) != 1:
                raise Usage("say where: --into <block>, --before <block> or --after <block> (%s goes "
                            "directly in %s)" % (block["label"], " or ".join(
                                self.vocab.label(t).lower() for t in block["within"] or [])))
            into = parents[0]["id"]
        node = {"id": node_id or new_id(self.document), "elType": block["kind"], "widgetType": block_type,
                "settings": {}, "elements": []}
        elements, at = self._place(into, position, before, after)
        elements.insert(at, node)
        for _ in range(max(0, int(columns or 0))):
            node["elements"].append({"id": new_id(self.document), "elType": "container",
                                     "widgetType": COLUMN, "settings": {}, "elements": []})
        held = [c["id"] for c in node["elements"]]
        message = "Added %s %s." % (self.describe(node), self._where(node["id"]))
        if held:
            message += " It holds %d columns: %s." % (len(held), ", ".join(held))
        return {"node": node["id"], "block": block["label"], "type": block_type, "added": True,
                "holds": held, "message": message}

    def remove(self, node_id):
        node, parent_list, index, _ancestors = self.node(node_id)
        if node.get("widgetType") == self.vocab.root:
            raise Usage("the Flyer block is the document itself; to start again, use new --from <design>")
        inside = sum(1 for _ in walk({"content": [node]})) - 1
        parent_list.pop(index)
        message = "Removed %s%s." % (self.describe(node), " and the %d blocks inside it" % inside if inside else "")
        return {"node": node_id, "block": self.vocab.label(node.get("widgetType")), "removed": True,
                "blocks_removed": inside + 1, "message": message}


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------


def tree_lines(vocab, document):
    lines = []
    pages = 0
    for node, _parent, _index, depth, _ancestors in walk(document):
        block_type = node.get("widgetType")
        label = vocab.label(block_type)
        settings = node.get("settings")
        count = len(settings) if isinstance(settings, (dict, list)) else 0
        extra = []
        if block_type == vocab.root:
            orientation = vocab.option(node, "orientation")
            extra.append("%s, %s" % (orientation, page_words(vocab, orientation)))
        elif block_type == "crecs_flyer_page":
            pages += 1
            label = "%s %d" % (label, pages)
            hidden = [band for band in ("header", "footer") if vocab.option(node, "show_" + band) == "hidden"]
            if hidden:
                extra.append("no %s band" % " or ".join(hidden))
        elif block_type == COLUMN and vocab.option(node, "width") is not None:
            extra.append("width %d%%" % vocab.option(node, "width"))
        if count:
            extra.append("%d setting%s" % (count, "" if count == 1 else "s"))
        lines.append("%s%s  %s%s" % ("  " * depth, node.get("id"), label,
                                     ("  · " + "; ".join(extra)) if extra else ""))
    return lines


def node_detail(vocab, document, node_id):
    node, _parent, _index, ancestors = find(document, node_id)
    block = vocab.block(node.get("widgetType")) or {}
    controls = block.get("controls", {})
    settings = node.get("settings") if isinstance(node.get("settings"), dict) else {}
    parts = {}
    for target, t in (block.get("targets") or {}).items():
        parts[target] = {"kinds": t["kinds"],
                         "properties": [spec["property"] for spec in controls.values()
                                        if spec.get("group") == "style" and spec.get("target") == target]}
    inside = ancestors[-1] if ancestors else None
    detail = {
        "id": node.get("id"),
        "block": block.get("label"),
        "type": node.get("widgetType"),
        "kind": block.get("kind"),
        "inside": "%s (%s)" % (vocab.label(inside.get("widgetType")), inside.get("id")) if inside else None,
        "holds": [c.get("id") for c in node.get("elements") or [] if isinstance(c, dict)],
        "settings": settings,
        "parts": parts,
        "texts": {slot: vocab.option(node, "text_" + slot) for slot in block.get("texts") or {}},
        "options": {name: {"value": settings.get(name), "default": controls[name].get("default")}
                    for name in block.get("options") or []},
    }
    if node.get("widgetType") == ROW:
        detail["widths"] = [vocab.option(c, "width") for c in Editor(vocab, document).columns(node)]
    return detail


def _allowed(vocab, spec):
    kind = spec["type"]
    if kind == "select":
        return "one of " + "|".join(spec["options"])
    if kind == "font":
        return "a font: " + "|".join(vocab.fonts)
    if kind == "number":
        unit = {"px": " px", "%": " %"}.get(spec.get("unit"), "")
        return "number %s..%s%s%s" % (spec["min"], spec["max"], unit, " or auto" if spec.get("auto") else "")
    if kind == "media":
        return "an image's number (crecs_preview.py media)"
    if kind == "fields":
        return "parts in order, from " + "|".join(spec["options"])
    if kind in ("slider", "dimensions"):
        return "%s %s..%s %s" % ("size" if kind == "slider" else "four sides", spec["min"], spec["max"],
                                 "|".join(u or '""' for u in spec["units"]))
    if kind == "text":
        default = (spec.get("default") or "").replace("\n", "\\n")
        return "%s (unset: \"%s\")" % ("text, line breaks as \\n" if spec.get("multiline") else "one line of text",
                                       default if len(default) <= 40 else default[:37] + "...")
    return kind


def control_rows(vocab, document, node_id, match=None):
    node, *_ = find(document, node_id)
    settings = node.get("settings") if isinstance(node.get("settings"), dict) else {}
    rows = []
    for name, spec in vocab.controls(node.get("widgetType")).items():
        if match and match.lower() not in name.lower():
            continue
        rows.append({"name": name, "allowed": _allowed(vocab, spec), "value": settings.get(name)})
    if node.get("widgetType") == ROW and (not match or match.lower() in "widths"):
        rows.append({"name": "widths", "allowed": "every column's width at once, in order: 60, 40 (auto to share)",
                     "value": [vocab.option(c, "width") for c in Editor(vocab, document).columns(node)]})
    return rows


# ---------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------


def _emit(payload, as_json, text):
    if as_json:
        print(json.dumps(payload, indent=1, ensure_ascii=False))
    else:
        text(payload)


def _print_findings(findings, out=None):
    out = out or sys.stderr
    for f in findings:
        where = (" [%s]" % f["node"]) if f.get("node") else ""
        print("  %s%s: %s" % (f["code"], where, f["message"]), file=out)


def build_parser():
    # SUPPRESS, so a value given before the command is not overwritten by the
    # subcommand's default: both `--file f show` and `show --file f` work.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--file", default=argparse.SUPPRESS,
                        help="the flyer layout file; defaults to $%s or ./%s" % (FILE_ENV, DEFAULT_FILE))
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="machine-readable output")

    parser = argparse.ArgumentParser(
        prog="crecs_flyer.py", parents=[common],
        description="Edit the property flyer's layout document, a local file. Offline, standard "
                    "library only: crecs_preview.py takes the file to the site's preview.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    def add(name, help_text):
        return sub.add_parser(name, help=help_text, description=help_text, parents=[common])

    add("blocks", "List every block a flyer can have.")

    p = add("show", "Show the flyer as a tree, or one block in detail.")
    p.add_argument("--node", help="a block id from the tree")

    p = add("controls", "List the settings one block takes, with what each accepts.")
    p.add_argument("--node", required=True)
    p.add_argument("--match", help="only settings whose name contains this")

    p = add("set", "Set one setting on one block. On a row, --key widths sets every column's "
                   "width at once; on a logo, --key media_id also makes the source the media library.")
    p.add_argument("--node", required=True)
    p.add_argument("--key", required=True, help="the setting, e.g. name_color, height, fields")
    p.add_argument("--value", required=True,
                   help="JSON, or shorthand: #0a3d62, 24px, '8px 16px', 320, auto, 'total_sf, rates'")

    p = add("unset", "Remove one setting from one block: the block's own value applies again.")
    p.add_argument("--node", required=True)
    p.add_argument("--key", required=True)

    p = add("text", "Change, or put back, one of a block's fixed texts.")
    p.add_argument("--node", required=True)
    p.add_argument("--slot", required=True, help="e.g. rates, phone_label, text")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--value", help="the text; write a line break as \\n where the text takes one")
    group.add_argument("--reset", action="store_true", help="the block's own text again")

    def placement(p):
        p.add_argument("--into", help="the container to put it in")
        p.add_argument("--position", type=int, help="with --into: 0 is first; default last")
        p.add_argument("--before", help="put it just before this block")
        p.add_argument("--after", help="put it just after this block")

    p = add("move", "Move a block somewhere else in the flyer.")
    p.add_argument("--node", required=True)
    placement(p)

    p = add("add", "Add a block, a row, a column or a page, with a fresh id.")
    p.add_argument("--type", required=True, dest="block_type",
                   help="the block, e.g. photo, crecs_flyer_photo_grid, row, column, page")
    placement(p)
    p.add_argument("--id", dest="node_id", help="the new block's id; generated by default")
    p.add_argument("--columns", type=int, default=0, help="with a row: add this many columns in it")

    p = add("remove", "Remove a block and everything inside it.")
    p.add_argument("--node", required=True)

    p = add("orientation", "Turn the designed pages landscape or portrait.")
    p.add_argument("value", metavar="landscape|portrait")

    add("validate", "Check the whole flyer the way the plugin will.")

    p = add("new", "Start the file from one of the plugin's built-in designs.")
    p.add_argument("--from", required=True, dest="source", help="the design's name")
    p.add_argument("--title", help="the flyer's title; the design's by default")
    p.add_argument("--force", action="store_true", help="replace the file if it exists")
    return parser


def _new(vocab, path, source, title, force, as_json):
    if not vocab.builtins:
        raise Usage("the flyer reference has no built-in designs yet, so there is nothing to start from")
    if source not in vocab.builtins:
        raise Usage("there is no built-in design %s; the designs are: %s" % (source, ", ".join(vocab.builtins)))
    if os.path.exists(path) and not force:
        raise Usage("%s already exists; pass --force to replace it" % path)
    document = copy.deepcopy(vocab.builtins[source])
    if title is not None:
        if not vocab.is_title(title):
            raise Usage("a title is one line of at most %d characters" % vocab.limits["title_max"])
        document["title"] = title
    findings = vocab.check(document)
    if blocking(findings):
        raise Refused("start from %s" % source, findings)
    save(path, document)
    root = document["content"][0]
    orientation = vocab.option(root, "orientation")
    pages = sum(1 for n in root.get("elements") or [] if isinstance(n, dict) and n.get("widgetType") == "crecs_flyer_page")
    result = {"file": path, "from": source, "title": document.get("title"), "orientation": orientation,
              "pages": pages, "message": "Wrote %s from the built-in design %s: %s, %d designed page%s."
              % (path, source, orientation, pages, "" if pages == 1 else "s")}
    _emit(result, as_json, lambda r: print(r["message"]))
    return EXIT_OK


def _utf8_streams():
    """Print UTF-8 whatever the pipe's code page.

    Windows gives a piped stdout its ANSI code page, which cannot print most of what a
    flyer's texts may hold (an emoji, an arrow), and the assistant reads the pipe as UTF-8.
    """
    for stream in (sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        if encoding != "utf8" and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            except (ValueError, OSError):
                pass


def main(argv=None):
    _utf8_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_USAGE
    args.file = getattr(args, "file", None)
    args.json = getattr(args, "json", False)

    try:
        vocab = Vocabulary.load()
    except FlyerLayoutError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_FILE

    if args.command == "blocks":
        rows = []
        for block_type, block in vocab.blocks.items():
            flags = [block["kind"]]
            if block["required"]:
                flags.append("required")
            if block["once"]:
                flags.append("once")
            if block.get("count"):
                flags.append("%d to %d" % tuple(block["count"]))
            if block["within"]:
                flags.append("in " + "/".join(vocab.label(t).lower() for t in block["within"]))
            rows.append({"type": block_type, "label": block["label"], "flags": flags,
                         "options": block["options"], "texts": list(block["texts"])})
        _emit(rows, args.json, lambda r: [print("%-24s %-18s %s" % (
            x["type"], x["label"], ", ".join(x["flags"]))) for x in r])
        return EXIT_OK

    path = args.file or default_file()

    try:
        if args.command == "new":
            return _new(vocab, path, args.source, args.title, args.force, args.json)
    except Usage as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print("refused: the plugin would not accept the flyer after this %s; nothing was written:" % exc,
              file=sys.stderr)
        _print_findings(exc.findings)
        return EXIT_REFUSED
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_FILE

    try:
        document = load(path)
    except FlyerLayoutError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_FILE

    editor = Editor(vocab, document)
    before = vocab.check(document)

    try:
        if args.command == "show":
            if args.node:
                detail = node_detail(vocab, document, args.node)

                def text(d):
                    print("%s  %s (%s)%s" % (d["id"], d["block"], d["type"],
                                              ", inside " + d["inside"] if d["inside"] else ""))
                    if d["holds"]:
                        print("holds: %s" % ", ".join(d["holds"]))
                    if "widths" in d:
                        print("column widths: %s" % ", ".join("auto" if w is None else "%d%%" % w
                                                              for w in d["widths"]))
                    for name, value in d["settings"].items():
                        print("  %s = %s" % (name, show_value(value)))
                    for target, part in d["parts"].items():
                        print("part %s (%s): %s" % (target, ", ".join(part["kinds"]),
                                                    ", ".join(part["properties"])))
                    for slot, value in d["texts"].items():
                        print('text %s: "%s"' % (slot, (value or "").replace("\n", "\\n")))
                    if d["options"]:
                        print("options: %s" % ", ".join(
                            "%s%s" % (name, "" if o["default"] is None else " (unset: %s)" % show_value(o["default"]))
                            for name, o in d["options"].items()))
                _emit(detail, args.json, text)
            else:
                lines = tree_lines(vocab, document)
                _emit({"tree": lines, "findings": before}, args.json,
                      lambda p: print("\n".join(p["tree"])))
            return EXIT_OK

        if args.command == "controls":
            rows = control_rows(vocab, document, args.node, args.match)
            _emit(rows, args.json, lambda r: [print("%-30s %-44s %s" % (
                x["name"], x["allowed"], "" if x["value"] is None else "= " + show_value(x["value"])))
                for x in r])
            return EXIT_OK

        if args.command == "validate":
            _emit({"findings": before, "ok": not blocking(before)}, args.json,
                  lambda p: (print("the flyer layout is valid") if p["ok"] else
                             (print("the plugin would refuse this flyer:"),
                              _print_findings(p["findings"], sys.stdout))))
            return EXIT_OK if not blocking(before) else EXIT_REFUSED

        if args.command == "set":
            result = editor.set(args.node, args.key, args.value)
        elif args.command == "unset":
            result = editor.unset(args.node, args.key)
        elif args.command == "text":
            result = editor.text(args.node, args.slot, args.value, args.reset)
        elif args.command == "move":
            result = editor.move(args.node, args.into, args.position, args.before, args.after)
        elif args.command == "add":
            result = editor.add(args.block_type, args.into, args.position, args.before, args.after,
                                args.node_id, args.columns)
        elif args.command == "remove":
            result = editor.remove(args.node)
        elif args.command == "orientation":
            result = editor.orientation(args.value)
        else:  # pragma: no cover - argparse guarantees one of the above
            raise Usage("unknown command %s" % args.command)

        remaining = editor.commit(before, args.command)
        save(path, document)
        _emit(result, args.json, lambda r: print(r["message"]))
        if blocking(remaining):
            # Taken because it made nothing worse; the preview still refuses until these go.
            print("written, but the plugin would still refuse the flyer:", file=sys.stderr)
            _print_findings(remaining)
        return EXIT_OK

    except Usage as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print("refused: the plugin would not accept the flyer after this %s; nothing was written:" % exc,
              file=sys.stderr)
        _print_findings(exc.findings)
        return EXIT_REFUSED
    except FlyerLayoutError as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_FILE
