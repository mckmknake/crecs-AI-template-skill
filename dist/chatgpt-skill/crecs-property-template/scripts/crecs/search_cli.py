"""crecs_search.py — edit the property search page's layout document.

The search page is previewed like the property template, through the site's Template
preview screen and crecs_preview.py, but what is edited is the plugin's own layout
document rather than an Elementor template (references/search/SEARCH-LAYOUT.md).

    crecs_preview.py --session-file <file> current --out search.json
    crecs_search.py --file search.json show
    crecs_search.py --file search.json set --node <id> --key button_background_color --value "#0a3d62"
    crecs_preview.py --session-file <file> apply --document search.json

Every change is checked against the plugin's vocabulary before it is written, and a
change that would make the plugin refuse the layout is not written at all, so the file
is always one the preview accepts. Nothing here talks to the site: crecs_preview.py
does. Nothing here publishes: a person does, with the Publish button in the preview.

Exit codes: 0 done, 1 refused (the layout would break), 2 bad request (unknown block,
setting or value), 3 file problem.
"""

import argparse
import difflib
import json
import os
import re
import sys
import tempfile

from . import __version__
from .search_layout import (DEVICES, SIDES, SearchLayoutError, Vocabulary, blocking, find,
                            new_id, normalise, settings_of, walk)

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2
EXIT_FILE = 3

FILE_ENV = "CRECS_SEARCH_FILE"
DEFAULT_FILE = "search-layout.json"


class Refused(Exception):
    """The change would make the plugin refuse the layout."""

    def __init__(self, message, findings):
        super().__init__(message)
        self.findings = findings


class Usage(Exception):
    """The request names something that does not exist, or a value that cannot be."""


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
        raise SearchLayoutError(
            "%s does not exist. Fetch the layout the preview shows first: "
            "crecs_preview.py --session-file <file> current --out %s" % (path, path))
    except (OSError, ValueError) as exc:
        raise SearchLayoutError("%s could not be read: %s" % (path, exc))
    if isinstance(document, dict) and "document" in document and "manifest" in document:
        document = document["document"]  # a saved export payload
    if not isinstance(document, dict) or document.get("type") != "crecs-search-layout":
        raise SearchLayoutError(
            "%s is not a search page layout. If it came from a property page preview, this "
            "is the wrong tool: use crecs_template.py." % path)
    return document


def save(path, document):
    normalise(document)
    folder = os.path.dirname(os.path.abspath(path))
    handle, temp = tempfile.mkstemp(prefix=".crecs-search-", suffix=".json", dir=folder)
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


def _length(token, spec):
    match = _LENGTH.match(token.strip())
    if not match:
        raise Usage("%r is not a length, such as 24px or 50%%" % token)
    unit = match.group(2)
    return _number(match.group(1)), unit


def parse_value(spec, raw):
    """A command-line value in the shape the control stores.

    JSON is taken as it is. Otherwise the familiar shorthand for the control's type: `24px`
    for a size, `8px 16px` for spacing on four sides, `0 2px 8px 0 rgba(0,0,0,0.2)` for a
    shadow, `yes` / `no` for a switch.
    """
    kind = spec["type"]
    try:
        parsed = json.loads(raw)
    except ValueError:
        parsed = raw

    if kind in ("color", "select", "font", "text"):
        return parsed if isinstance(parsed, str) else raw
    if kind == "switch":
        word = str(parsed).strip().lower() if not isinstance(parsed, bool) else ("yes" if parsed else "no")
        if word in ("yes", "true", "on", "1"):
            return "yes"
        if word in ("no", "false", "off", "0", ""):
            return None
        raise Usage("say yes or no")
    if kind == "number":
        if isinstance(parsed, int) and not isinstance(parsed, bool):
            return parsed
        raise Usage("must be a whole number")
    if kind == "slider":
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, (int, float)) and not isinstance(parsed, bool):
            return {"unit": _default_unit(spec), "size": parsed}
        size, unit = _length(str(parsed), spec)
        return {"unit": unit if unit or "" in spec["units"] else _default_unit(spec), "size": size}
    if kind == "dimensions":
        if isinstance(parsed, dict):
            return parsed
        tokens = str(parsed).split()
        if not 1 <= len(tokens) <= 4:
            raise Usage("give one to four lengths, as in CSS: 8px, 8px 16px, or 1px 2px 3px 4px")
        lengths = [_length(t, spec) for t in tokens]
        units = {u for n, u in lengths if u or n != 0}
        if len(units) > 1:
            raise Usage("all four sides need the same unit")
        unit = units.pop() if units else _default_unit(spec)
        unit = unit or _default_unit(spec)
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
    if kind == "shadow":
        if isinstance(parsed, dict):
            return parsed
        tokens = str(parsed).split(None, 4)
        if len(tokens) < 5:
            raise Usage("give horizontal, vertical, blur and spread in pixels, then a colour: "
                        "0 2px 8px 0 rgba(0,0,0,0.2)")
        values = []
        for token in tokens[:4]:
            number, unit = _length(token, spec)
            if unit not in ("", "px"):
                raise Usage("a shadow is measured in pixels")
            values.append(number)
        return {"horizontal": values[0], "vertical": values[1], "blur": values[2],
                "spread": values[3], "color": tokens[4].strip()}
    return parsed


def show_value(value):
    if isinstance(value, dict) and "size" in value and "unit" in value and len(value) <= 3:
        return "%s%s" % (value["size"], value["unit"])
    if isinstance(value, dict) and all(side in value for side in SIDES):
        return " ".join("%s%s" % (value[s], value.get("unit", "")) for s in SIDES)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


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
        except SearchLayoutError as exc:
            raise Usage(str(exc))

    def label(self, node):
        return self.vocab.label(node.get("widgetType"))

    def describe(self, node):
        return "%s (%s)" % (self.label(node), node.get("id"))

    def control_name(self, node, key, device=None, hover=False):
        controls = self.vocab.controls(node.get("widgetType"))
        base = key + ("_hover" if hover and not key.endswith("_hover") else "")
        name = base + ("_" + device if device and not base.endswith("_" + device) else "")
        if name in controls:
            return name, controls[name]
        if device and base in controls:
            raise Usage("%s has one %s for every device: leave --device out"
                        % (self.describe(node), base))
        close = difflib.get_close_matches(name, list(controls), n=4, cutoff=0.6)
        hint = " Did you mean: %s?" % ", ".join(close) if close else \
            " List them with: controls --node %s" % node.get("id")
        raise Usage("%s has no %s setting.%s" % (self.describe(node), name, hint))

    # -- checks --------------------------------------------------------------

    def commit(self, before, what):
        """Refuse the change if it brings a finding the document did not have."""
        after = self.vocab.check(self.document)
        new = [f for f in after if f not in before]
        if blocking(new):
            raise Refused(what, new)
        return after

    # -- edits ---------------------------------------------------------------

    def set(self, node_id, key, raw, device=None, hover=False):
        node, *_ = self.node(node_id)
        name, spec = self.control_name(node, key, device, hover)
        value = parse_value(spec, raw)
        if value is None:
            return self.unset(node_id, name)
        problem = self.vocab.problem(spec, value)
        if problem:
            raise Usage("%s: %s %s" % (self.describe(node), name, problem))
        settings_of(node)[name] = value
        return {"node": node["id"], "block": self.label(node), "setting": name, "value": value}

    def unset(self, node_id, key, device=None, hover=False):
        node, *_ = self.node(node_id)
        name, _spec = self.control_name(node, key, device, hover)
        settings = settings_of(node)
        had = name in settings
        settings.pop(name, None)
        return {"node": node["id"], "block": self.label(node), "setting": name, "removed": had}

    def text(self, node_id, slot, value=None, reset=False):
        node, *_ = self.node(node_id)
        texts = self.vocab.block(node.get("widgetType")).get("texts") or {}
        if slot not in texts:
            have = ", ".join(texts) if texts else "none"
            raise Usage("%s has no %s text (its texts: %s)" % (self.describe(node), slot, have))
        if reset:
            return self.unset(node_id, "text_" + slot)
        return self.set(node_id, "text_" + slot, json.dumps(value, ensure_ascii=False))

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
        anchor, parent_list, index, _ancestors = self.node(anchor_id)
        return parent_list, index + (1 if after is not None else 0)

    def move(self, node_id, into=None, position=None, before=None, after=None):
        node, parent_list, index, _ancestors = self.node(node_id)
        if node.get("widgetType") == "crecs_search_page":
            raise Usage("the page block is the root; everything else moves inside it")
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
        return self._with_hint({"node": node_id, "block": self.label(node), "moved": True}, node_id)

    def _with_hint(self, result, node_id):
        """Say so when a block lands in a container that still has the page's own layout.

        A container the document gives no direction, gap… keeps the arrangement the page's
        stylesheet was written for, which knows nothing of the block just put there: the
        main area, for one, is a fixed-height column that wraps. Giving the container a
        direction hands its layout to the document.
        """
        _node, _list, _index, ancestors = find(self.document, node_id)
        if not ancestors:
            return result
        parent = ancestors[-1]
        block = self.vocab.block(parent.get("widgetType")) or {}
        settings = parent.get("settings") if isinstance(parent.get("settings"), dict) else {}
        layout = ("direction", "wrap", "gap", "justify", "align")
        managed = any(name.split("_")[0] in layout for name in settings if not name.startswith("_"))
        # A box is always the document's own; the page lays it out whatever it says.
        if block.get("lays_out") and not managed and parent.get("widgetType") != self.vocab.box:
            result["hint"] = ("%s still has the page's original arrangement, which was not made "
                              "for this. Give it a direction so the layout decides: set --node %s "
                              "--key direction --value column (or row)"
                              % (self.describe(parent), parent.get("id")))
        return result

    def add_box(self, into=None, position=None, before=None, after=None, wrap=None,
                direction=None, box_id=None):
        wrap = [w for w in (wrap or []) if w]
        if box_id is not None and not self.vocab.is_id(box_id):
            raise Usage("a block id is 4 to 16 letters or digits")
        box = {"id": box_id or new_id(self.document), "elType": "container",
               "widgetType": self.vocab.box, "settings": {}, "elements": []}
        if direction:
            spec = self.vocab.controls(self.vocab.box)["direction"]
            problem = self.vocab.problem(spec, direction)
            if problem:
                raise Usage("direction %s" % problem)
            box["settings"]["direction"] = direction
        if into is None and before is None and after is None:
            if not wrap:
                raise Usage("say where: --into <block>, --before <block>, --after <block>, "
                            "or --wrap the blocks it should hold")
            before = wrap[0]  # where the first wrapped block is now
        elements, at = self._place(into, position, before, after)
        elements.insert(at, box)
        _box, _list, _index, box_ancestors = find(self.document, box["id"])
        for node_id in wrap:
            if node_id == box["id"]:
                continue
            node, parent_list, index, ancestors = self.node(node_id)
            if node.get("widgetType") == "crecs_search_page":
                raise Usage("the page block cannot go inside a box")
            if any(a is node for a in box_ancestors):
                raise Usage("a box cannot hold the block it sits in")
            parent_list.pop(index)
            box["elements"].append(node)
        return self._with_hint({"node": box["id"], "block": self.vocab.label(self.vocab.box),
                                "added": True, "holds": [n.get("id") for n in box["elements"]]},
                               box["id"])

    def remove_box(self, node_id):
        node, parent_list, index, _ancestors = self.node(node_id)
        if node.get("widgetType") != self.vocab.box:
            raise Usage("%s is not a box. Only a box can be removed: every other block is "
                        "part of how the page works" % self.describe(node))
        children = node.get("elements") if isinstance(node.get("elements"), list) else []
        parent_list[index:index + 1] = children
        return {"node": node_id, "removed": True, "released": [c.get("id") for c in children]}

    def hide(self, node_id, device, hidden=True):
        return self.set(node_id, "_hide_" + device, "yes" if hidden else "no") if hidden else \
            self.unset(node_id, "_hide_" + device)


# ---------------------------------------------------------------------------
# reading
# ---------------------------------------------------------------------------


def tree_lines(vocab, document):
    lines = []
    for node, _parent, _index, depth, _ancestors in walk(document):
        settings = node.get("settings")
        count = len(settings) if isinstance(settings, (dict, list)) else 0
        hidden = [d for d in ("desktop",) + DEVICES
                  if isinstance(settings, dict) and settings.get("_hide_" + d) == "yes"]
        extra = []
        if count:
            extra.append("%d setting%s" % (count, "" if count == 1 else "s"))
        if hidden:
            extra.append("hidden on " + ", ".join(hidden))
        lines.append("%s%s  %s%s" % ("  " * depth, node.get("id"), vocab.label(node.get("widgetType")),
                                     ("  · " + "; ".join(extra)) if extra else ""))
    return lines


def node_detail(vocab, document, node_id):
    node, _parent, _index, ancestors = find(document, node_id)
    block = vocab.block(node.get("widgetType")) or {}
    controls = block.get("controls", {})
    settings = node.get("settings") if isinstance(node.get("settings"), dict) else {}
    targets = block.get("targets") or {}
    parts = {}
    for target, t in targets.items():
        names = sorted({name[len(target) + 1:] for name, spec in controls.items()
                        if spec.get("group") == "style" and spec.get("target") == target
                        and spec.get("state") == "" and spec.get("device") == ""})
        parts[target] = {"kinds": t["kinds"], "hover": t["hover"], "properties": names}
    return {
        "id": node.get("id"),
        "block": block.get("label"),
        "type": node.get("widgetType"),
        "kind": block.get("kind"),
        "required": block.get("required"),
        "inside": vocab.label(ancestors[-1].get("widgetType")) if ancestors else None,
        "holds": [c.get("id") for c in node.get("elements") or [] if isinstance(c, dict)],
        "settings": settings,
        "parts": parts,
        "box": [n for n in ("_margin", "_padding", "_width", "_grow", "_order") if n in controls],
        "layout": [n for n in ("direction", "wrap", "gap", "justify", "align") if n in controls],
        "map": "map_height" in controls,
        "hide": [d for d in ("desktop",) + DEVICES if "_hide_" + d in controls],
        "texts": {slot: settings.get("text_" + slot) or default
                  for slot, default in (block.get("texts") or {}).items()},
    }


def control_rows(vocab, document, node_id, match=None):
    node, *_ = find(document, node_id)
    settings = node.get("settings") if isinstance(node.get("settings"), dict) else {}
    rows = []
    for name, spec in vocab.controls(node.get("widgetType")).items():
        if match and match.lower() not in name.lower():
            continue
        allowed = spec["type"]
        if spec["type"] == "select":
            allowed = "one of " + "|".join(spec["options"])
        elif spec["type"] in ("slider", "dimensions"):
            allowed = "%s %s..%s %s" % (spec["type"], spec["min"], spec["max"],
                                        "|".join(u or '""' for u in spec["units"]))
        elif spec["type"] == "number":
            allowed = "number %s..%s" % (spec["min"], spec["max"])
        elif spec["type"] == "text":
            allowed = 'text (page shows "%s")' % spec.get("default", "")
        rows.append({"name": name, "allowed": allowed, "value": settings.get(name)})
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
                        help="the layout file; defaults to $%s or ./%s" % (FILE_ENV, DEFAULT_FILE))
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="machine-readable output")

    parser = argparse.ArgumentParser(
        prog="crecs_search.py", parents=[common],
        description="Edit the property search page's layout document. Offline, standard "
                    "library only. Fetch the file with crecs_preview.py current, send it "
                    "back with crecs_preview.py apply.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    def add(name, help_text):
        return sub.add_parser(name, help=help_text, description=help_text, parents=[common])

    add("blocks", "List every block the search page can have.")

    p = add("show", "Show the layout as a tree, or one block in detail.")
    p.add_argument("--node", help="a block id from the tree")

    p = add("controls", "List the settings one block takes, with what each accepts.")
    p.add_argument("--node", required=True)
    p.add_argument("--match", help="only settings whose name contains this")

    for name, help_text in (("set", "Set one setting on one block."),
                            ("unset", "Remove one setting from one block: the page goes back "
                                      "to how it looks without it.")):
        p = add(name, help_text)
        p.add_argument("--node", required=True)
        p.add_argument("--key", required=True,
                       help="the setting, without a device suffix, e.g. button_background_color")
        if name == "set":
            p.add_argument("--value", required=True,
                           help="JSON, or shorthand: #0a3d62, 24px, '8px 16px', yes")
        p.add_argument("--device", choices=list(DEVICES),
                       help="the tablet or mobile value; desktop is the default")
        p.add_argument("--hover", action="store_true", help="the value on mouse-over")

    p = add("text", "Change, or put back, one of the page's texts.")
    p.add_argument("--node", required=True)
    p.add_argument("--slot", required=True, help="e.g. button, placeholder, label")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--value")
    group.add_argument("--reset", action="store_true", help="the page's own text again")

    def placement(p):
        p.add_argument("--into", help="the container to put it in")
        p.add_argument("--position", type=int, help="with --into: 0 is first; default last")
        p.add_argument("--before", help="put it just before this block")
        p.add_argument("--after", help="put it just after this block")

    p = add("move", "Move a block somewhere else on the page.")
    p.add_argument("--node", required=True)
    placement(p)

    p = add("add-box", "Add a box: a container that lays out the blocks it holds.")
    placement(p)
    p.add_argument("--wrap", help="comma-separated block ids to put in it, in order")
    p.add_argument("--direction", choices=["row", "column"])
    p.add_argument("--id", dest="box_id", help="the new box's id; generated by default")

    p = add("remove-box", "Remove a box; the blocks it held take its place.")
    p.add_argument("--node", required=True)

    for name, help_text in (("hide", "Hide a block on one device."),
                            ("unhide", "Show a hidden block on that device again.")):
        p = add(name, help_text)
        p.add_argument("--node", required=True)
        p.add_argument("--device", required=True, choices=["desktop"] + list(DEVICES))

    add("validate", "Check the whole layout the way the plugin will.")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return EXIT_USAGE
    args.file = getattr(args, "file", None)
    args.json = getattr(args, "json", False)

    try:
        vocab = Vocabulary.load()
    except SearchLayoutError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_FILE

    if args.command == "blocks":
        rows = []
        for block_type, block in vocab.blocks.items():
            flags = [block["kind"], "required" if block["required"] else "optional"]
            if block["repeatable"]:
                flags.append("repeatable")
            if block["within"]:
                flags.append("inside the filters")
            if block["lays_out"]:
                flags.append("lays out")
            rows.append({"type": block_type, "label": block["label"], "flags": flags,
                         "texts": list(block["texts"])})
        _emit(rows, args.json, lambda r: [print("%-34s %-28s %s" % (
            x["type"], x["label"], ", ".join(x["flags"]))) for x in r])
        return EXIT_OK

    path = args.file or default_file()
    try:
        document = load(path)
    except SearchLayoutError as exc:
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
                    for name, value in d["settings"].items():
                        print("  %s = %s" % (name, show_value(value)))
                    for target, part in d["parts"].items():
                        print("part %s%s: %s" % (target, " (hover too)" if part["hover"] else "",
                                                ", ".join(part["properties"])))
                    if d["box"]:
                        print("its box: %s" % ", ".join(d["box"]))
                    if d["layout"]:
                        print("lays out its blocks: %s" % ", ".join(d["layout"]))
                    if d["map"]:
                        print("map height: map_height")
                    if d["hide"]:
                        print("can be hidden on: %s" % ", ".join(d["hide"]))
                    for slot, value in d["texts"].items():
                        print('text %s: "%s"' % (slot, value))
                _emit(detail, args.json, text)
            else:
                lines = tree_lines(vocab, document)
                _emit({"tree": lines, "findings": before}, args.json,
                      lambda p: print("\n".join(p["tree"])))
            return EXIT_OK

        if args.command == "controls":
            rows = control_rows(vocab, document, args.node, args.match)
            _emit(rows, args.json, lambda r: [print("%-44s %-40s %s" % (
                x["name"], x["allowed"], "" if x["value"] is None else "= " + show_value(x["value"])))
                for x in r])
            return EXIT_OK

        if args.command == "validate":
            _emit({"findings": before, "ok": not blocking(before)}, args.json,
                  lambda p: (print("the layout is valid") if p["ok"] else
                             (print("the plugin would refuse this layout:"),
                              _print_findings(p["findings"], sys.stdout))))
            return EXIT_OK if not blocking(before) else EXIT_REFUSED

        if args.command == "set":
            result = editor.set(args.node, args.key, args.value, args.device, args.hover)
        elif args.command == "unset":
            result = editor.unset(args.node, args.key, args.device, args.hover)
        elif args.command == "text":
            result = editor.text(args.node, args.slot, args.value, args.reset)
        elif args.command == "move":
            result = editor.move(args.node, args.into, args.position, args.before, args.after)
        elif args.command == "add-box":
            wrap = [w.strip() for w in (args.wrap or "").split(",") if w.strip()]
            result = editor.add_box(args.into, args.position, args.before, args.after, wrap,
                                    args.direction, args.box_id)
        elif args.command == "remove-box":
            result = editor.remove_box(args.node)
        elif args.command in ("hide", "unhide"):
            result = editor.hide(args.node, args.device, args.command == "hide")
        else:  # pragma: no cover - argparse guarantees one of the above
            raise Usage("unknown command %s" % args.command)

        editor.commit(before, args.command)
        save(path, document)
        _emit(result, args.json, lambda r: print(json.dumps(r, ensure_ascii=False)))
        return EXIT_OK

    except Usage as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    except Refused as exc:
        print("refused: the plugin would not accept the layout after this %s; nothing was "
              "written:" % exc, file=sys.stderr)
        _print_findings(exc.findings)
        return EXIT_REFUSED
    except SearchLayoutError as exc:
        print("refused: %s" % exc, file=sys.stderr)
        return EXIT_USAGE
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return EXIT_FILE
