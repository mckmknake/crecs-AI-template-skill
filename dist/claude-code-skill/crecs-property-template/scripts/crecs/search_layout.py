"""The property search page's layout document: vocabulary, checks and tree edits.

The search page (the site's search slug, usually /properties) is not an Elementor page.
The plugin draws it from a layout document — a tree of the page's blocks in Elementor's
shape — that says where each block goes, how it looks and what its texts say. See
references/search/SEARCH-LAYOUT.md.

Everything this module knows about blocks and controls comes from
references/search/search-layout.json, which the plugin generates from its own registry.
Nothing here is hand-maintained: if a block or a control is missing, the answer is to
regenerate that file from the plugin, never to add it here.

`problem()` and `check()` are ports of the plugin's Crecs_Search_Layout_Controls::problem()
and Crecs_Search_Layout_Validate::check(), and must agree with them word for word.
tests/test_search.py holds them to the plugin's own verdicts in
tests/fixtures/search-vectors.json. The plugin checks every revision again whatever this
module concluded; checking here is what lets the assistant say what is wrong before
anything is sent.
"""

import json
import os
import random
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(_HERE))  # skill root
REFERENCE = os.path.join(_PACKAGE_ROOT, "references", "search", "search-layout.json")

DEVICES = ("tablet", "mobile")
SIDES = ("top", "right", "bottom", "left")

# PCRE's \s and \d without the u modifier: ASCII only, which Python's are not.
_WS = r"[ \t\n\x0b\x0c\r]*"
_BYTE = _WS + r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})" + _WS
_ALPHA = _WS + r"(?:0|1|0?\.[0-9]{1,3}|1\.0{1,3})" + _WS
# `$` without re.MULTILINE also matches before a final newline, as PCRE's does.
_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGB = re.compile(r"^rgba?\(" + _BYTE + "," + _BYTE + "," + _BYTE + "(?:," + _ALPHA + r")?\)$")
_NUMBER = re.compile(r"^-?[0-9]{1,5}(?:\.[0-9]{1,3})?$")
# PCRE's `$` with the D modifier: the very end, a final newline refused.
_MAP_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")
_CONTROL_CHAR = re.compile(r"[\x00-\x1f\x7f]")


class SearchLayoutError(Exception):
    """A document or an edit this module refuses."""


class Vocabulary:
    """The plugin's registry, as references/search/search-layout.json records it."""

    def __init__(self, data):
        self.data = data
        self.blocks = data["blocks"]
        self.fonts = data["fonts"]
        self.limits = data["limits"]
        self.devices = data["devices"]
        self.filters = data["filters"]
        self.box = data["box"]
        self.builtin = data["builtin"]
        self._id = re.compile(
            self.limits["id_pattern"],
            re.IGNORECASE if "i" in self.limits.get("id_flags", "") else 0)

    @classmethod
    def load(cls, path=REFERENCE):
        try:
            with open(path, encoding="utf-8") as fh:
                return cls(json.load(fh))
        except (OSError, ValueError, KeyError) as exc:
            raise SearchLayoutError("the search layout reference could not be read (%s): %s"
                                    % (path, exc))

    def block(self, block_type):
        return self.blocks.get(block_type)

    def controls(self, block_type):
        block = self.blocks.get(block_type)
        return block["controls"] if block else {}

    def label(self, block_type):
        block = self.blocks.get(block_type)
        return block["label"] if block else block_type

    def is_id(self, value):
        return isinstance(value, str) and self._id.match(value) is not None

    # -- values -------------------------------------------------------------------

    def problem(self, spec, value):
        """'' when `value` is acceptable for the control `spec`, otherwise why not."""
        if is_unset(spec, value):
            return ""
        kind = spec["type"]
        if kind == "color":
            return "" if is_color(value) else \
                "is not a colour (#rgb, #rrggbb, #rrggbbaa, rgb(), rgba() or transparent)"
        if kind == "select":
            return "" if isinstance(value, str) and value in spec["options"] else \
                "must be one of: " + ", ".join(spec["options"])
        if kind == "font":
            return "" if isinstance(value, str) and value in self.fonts else \
                "must be one of the fonts the site offers: " + ", ".join(self.fonts)
        if kind in ("switch", "hide"):
            return "" if value == "yes" else "must be 'yes' or empty"
        if kind == "amount":
            ok = isinstance(value, (int, float)) and not isinstance(value, bool) \
                and 0 <= value <= self.limits["amount_max"]
            return "" if ok else "must be a number from 0 to %d" % self.limits["amount_max"]
        if kind == "list":
            return self._list_problem(value)
        if kind == "fields":
            return self._fields_problem(spec, value)
        if kind == "decimal":
            ok = isinstance(value, (int, float)) and not isinstance(value, bool) \
                and spec["min"] <= value <= spec["max"]
            return "" if ok else "must be a number from %d to %d" % (spec["min"], spec["max"])
        if kind == "map_color":
            # Google's map styles take a hex colour and nothing else.
            ok = isinstance(value, str) and _MAP_COLOR.match(value) is not None
            return "" if ok else "must be a colour written #rrggbb or #rgb"
        if kind == "number":
            ok = _is_int(value) and spec["min"] <= value <= spec["max"]
            return "" if ok else "must be a whole number from %d to %d" % (spec["min"], spec["max"])
        if kind == "slider":
            if not isinstance(value, dict) or "unit" not in value \
                    or not _strict_in(value["unit"], spec["units"]):
                return 'must be {"unit": one of ' + _units(spec) + ', "size": a number}'
            if _in_range(value.get("size"), spec, value["unit"]):
                return ""
            return _range_text(spec, value["unit"])
        if kind == "dimensions":
            if not isinstance(value, dict) or "unit" not in value \
                    or not _strict_in(value["unit"], spec["units"]):
                return ('must be {"unit": one of ' + _units(spec)
                        + ', "top", "right", "bottom", "left": numbers}')
            for side in SIDES:
                if side not in value or not _in_range(value[side], spec, value["unit"]):
                    return "'%s' %s" % (side, _range_text(spec, value["unit"]))
            if value.get("isLinked") is not None and not isinstance(value["isLinked"], bool):
                return "'isLinked' must be true or false"
            return ""
        if kind == "shadow":
            if not isinstance(value, (dict, list)):
                return 'must be {"horizontal", "vertical", "blur", "spread": pixels, "color": a colour}'
            parts = value if isinstance(value, dict) else {}
            for part, low, high in (("horizontal", -50, 50), ("vertical", -50, 50),
                                    ("blur", 0, 100), ("spread", -50, 50)):
                v = parts.get(part)
                if v is None or not is_number(v) or float(v) < low or float(v) > high:
                    return "'%s' must be a number from %d to %d" % (part, low, high)
            return "" if is_color(parts.get("color")) else "'color' is not a colour"
        if kind == "text":
            if not isinstance(value, str):
                return "must be text"
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                return "must be one line of at most %d characters" % self.limits["text_max"]
            if _CONTROL_CHAR.search(value) or len(value) > self.limits["text_max"]:
                return "must be one line of at most %d characters" % self.limits["text_max"]
            return ""
        return "has a type this plugin does not know"

    def _list_problem(self, value):
        """Why a list of names is not acceptable, or ''. Names compare as name_key() has them."""
        items = php_list(value)
        if items is None:
            return "must be a list of names"
        if len(items) > self.limits["list_max"]:
            return "must hold at most %d names" % self.limits["list_max"]
        seen = set()
        for item in items:
            if not isinstance(item, str) or _php_trim(item) == "" or not _is_utf8(item) \
                    or _CONTROL_CHAR.search(item) or len(item) > self.limits["text_max"]:
                return "must hold names of one line, at most %d characters each" % self.limits["text_max"]
            key = name_key(item)
            if key in seen:
                return 'names "%s" twice' % item
            seen.add(key)
        return ""

    @staticmethod
    def _fields_problem(spec, value):
        """Why a choice of parts is not acceptable, or ''. Each part once, in its order."""
        parts = ", ".join(spec["options"])
        items = php_list(value)
        if items is None:
            return "must be a list of parts from: " + parts
        seen = set()
        for item in items:
            if not isinstance(item, str) or item not in spec["options"]:
                if isinstance(item, str):
                    return 'has no part "%s"; its parts are: %s' % (item, parts)
                return "must be a list of parts from: " + parts
            if item in seen:
                return 'names "%s" twice' % item
            seen.add(item)
        return ""

    # -- documents ----------------------------------------------------------------

    def check(self, document):
        """Every finding for a document, as the plugin reports them."""
        out = []
        if not isinstance(document, dict) or document.get("type") != "crecs-search-layout" \
                or not (_is_int(document.get("version")) and document.get("version") == 1) \
                or not isinstance(document.get("content"), (list, dict)):
            out.append(_finding("E-SL-SHAPE", None,
                                'Not a search layout document: it needs "type": '
                                '"crecs-search-layout", "version": 1 and a "content" list.'))
            return out

        content = document["content"]
        nodes = _values(content)
        first = content.get("0") if isinstance(content, dict) else (content[0] if content else None)
        if len(nodes) != 1 or not isinstance(first, dict) or first.get("widgetType") is None \
                or first["widgetType"] != "crecs_search_page":
            out.append(_finding("E-SL-ROOT", None,
                                "The content must be exactly one crecs_search_page block, "
                                "with everything else inside it."))

        state = {"ids": set(), "counts": {}, "nodes": 0, "depth": 0, "starts": [], "clear_hidden": []}
        self._walk(nodes, [], state, out)

        for block_type, block in self.blocks.items():
            n = state["counts"].get(block_type, 0)
            if block["required"] and n == 0:
                out.append(_finding(
                    "E-SL-REQUIRED", None,
                    'The page needs the "%s" block (%s): what it carries is used by the '
                    "search, the map or the SEO." % (block["label"], block_type)))
            if not block["repeatable"] and n > 1:
                out.append(_finding(
                    "E-SL-ONCE", None,
                    'The "%s" block (%s) appears %d times; it may appear once, because it '
                    "carries ids the page's scripts look up." % (block["label"], block_type, n)))
        # A filter may start with a value, and visitors must always be able to remove it:
        # by the filter itself, or by Clear. Unseen where Clear is unseen too, they could not.
        for start in state["starts"]:
            stuck = [device for device in start["devices"] if device in state["clear_hidden"]]
            if stuck:
                out.append(_finding(
                    "E-SL-STUCK", start["node"],
                    'The "%s" block starts with a value that cannot be seen on %s, where Clear '
                    "cannot be seen either: visitors there could never remove it."
                    % (start["label"], ", ".join(stuck))))
        if state["nodes"] > self.limits["max_nodes"] or state["depth"] > self.limits["max_depth"]:
            out.append(_finding(
                "E-SL-LIMIT", None,
                "The document has %d blocks nested %d deep; at most %d blocks, %d deep."
                % (state["nodes"], state["depth"], self.limits["max_nodes"],
                   self.limits["max_depth"])))
        return out

    def _walk(self, nodes, ancestors, state, out, hidden_above=()):
        """`hidden_above`: the devices where a box around these nodes is hidden."""
        state["depth"] = max(state["depth"], len(ancestors) + 1)
        for node in nodes:
            state["nodes"] += 1
            if not isinstance(node, dict) or node.get("id") is None or node.get("elType") is None \
                    or node.get("widgetType") is None or not isinstance(node["widgetType"], str) \
                    or not isinstance(node.get("settings"), (dict, list)) \
                    or not isinstance(node.get("elements"), (dict, list)):
                node_id = node.get("id") if isinstance(node, dict) and isinstance(node.get("id"), str) else None
                out.append(_finding("E-SL-NODE", node_id,
                                    'A block must have an "id", an "elType", a "widgetType", '
                                    'a "settings" object and an "elements" list.'))
                continue

            node_id = node["id"]
            if not self.is_id(node_id):
                out.append(_finding("E-SL-ID", None, "A block id must be 4 to 16 letters or digits."))
                node_id = None
            elif node_id in state["ids"]:
                out.append(_finding("E-SL-ID", node_id,
                                    "The id %s is used by more than one block." % node_id))
            else:
                state["ids"].add(node_id)

            block_type = node["widgetType"]
            block = self.blocks.get(block_type)
            if block is None:
                out.append(_finding("E-SL-BLOCK", node_id, 'There is no "%s" block.' % block_type))
                continue
            state["counts"][block_type] = state["counts"].get(block_type, 0) + 1

            if block["kind"] != node["elType"]:
                out.append(_finding("E-SL-ELTYPE", node_id, "%s is a %s, not a %s."
                                    % (block_type, block["kind"], _php_string(node["elType"]))))
            elements = _values(node["elements"])
            if block["kind"] == "widget" and elements:
                out.append(_finding("E-SL-CHILDREN", node_id,
                                    "%s cannot hold other blocks." % block_type))
            if block_type == "crecs_search_page" and ancestors:
                out.append(_finding("E-SL-ROOT", node_id,
                                    "The page block can only be the document's root."))
            if block["within"] and block["within"] not in ancestors:
                out.append(_finding(
                    "E-SL-WITHIN", node_id,
                    'The "%s" block must stay inside the filters: Clear resets and walks the '
                    "filters form." % block["label"]))
            if self.filters in ancestors and not block["within"] and block_type != self.box:
                out.append(_finding(
                    "E-SL-NOT-WITHIN", node_id,
                    'The "%s" block cannot go inside the filters: Clear would reset it with '
                    "them." % block["label"]))

            controls = block["controls"]
            for name, value in _items(node["settings"]):
                if name not in controls:
                    out.append(_finding("E-SL-SETTING", node_id,
                                        '%s has no "%s" setting.' % (block_type, name)))
                    continue
                problem = self.problem(controls[name], value)
                if problem:
                    out.append(_finding("E-SL-VALUE", node_id,
                                        '%s "%s" %s.' % (block_type, name, problem)))

            # Where visitors cannot see this block: where it, or a box around it, is hidden.
            settings = dict(_items(node["settings"]))
            hidden = [device for device in ("desktop", "tablet", "mobile")
                      if device in hidden_above
                      or ("_hide_" + device in controls and settings.get("_hide_" + device) == "yes")]

            self._check_together(block_type, node_id, block, settings, controls, hidden, state, out)

            if elements:
                self._walk(elements, ancestors + [block_type], state, out, hidden)

    def _check_together(self, block_type, node_id, block, settings, controls, hidden, state, out):
        """Rules between one block's settings, and what the Clear rule needs to know.

        A setting that is itself refused, or not set, takes no part.
        """
        def is_set(name):
            return name in controls and settings.get(name) is not None \
                and not is_unset(controls[name], settings[name]) \
                and self.problem(controls[name], settings[name]) == ""

        def on(name):
            return is_set(name) and settings[name] == "yes"

        # Every name a list starts with must be one the list offers, or it would be checked
        # where nobody could uncheck it.
        if is_set("offer") and is_set("start_checked"):
            offered = {name_key(name) for name in php_list(settings["offer"])}
            for name in php_list(settings["start_checked"]):
                if name_key(name) not in offered:
                    out.append(_finding(
                        "E-SL-VALUE", node_id,
                        '%s "start_checked" names "%s", which "offer" does not list, so '
                        "visitors could not uncheck it." % (block_type, name)))
                    break

        if is_set("start_min") and is_set("start_max") and settings["start_min"] > settings["start_max"]:
            out.append(_finding("E-SL-VALUE", node_id,
                                '%s "start_min" is larger than "start_max".' % block_type))

        # A filter whose two choices are both hidden is a hidden filter: say so. Otherwise
        # the unit the page starts with must be one visitors can see.
        both_hidden = False
        for first, second in (("for_sale_option_hide", "for_lease_option_hide"),
                              ("square_feet_option_hide", "acres_option_hide")):
            if first in controls and on(first) and on(second):
                out.append(_finding("E-SL-VALUE", node_id,
                                    "%s hides both of its choices: hide the whole block instead."
                                    % block_type))
                both_hidden = True
        if "start_unit" in controls and not both_hidden:
            unit = settings["start_unit"] if is_set("start_unit") else "square_feet"
            if on(unit + "_option_hide"):
                out.append(_finding("E-SL-VALUE", node_id,
                                    "%s starts in %s, whose choice is hidden." % (block_type, unit)))

        # Stage 3: the map's zoom stays within its limits, and a centre is a place.
        if is_set("map_min_zoom") and is_set("map_max_zoom") \
                and settings["map_min_zoom"] > settings["map_max_zoom"]:
            out.append(_finding("E-SL-VALUE", node_id,
                                '%s "map_min_zoom" is larger than "map_max_zoom".' % block_type))
        elif is_set("map_zoom") and (
                (is_set("map_min_zoom") and settings["map_zoom"] < settings["map_min_zoom"])
                or (is_set("map_max_zoom") and settings["map_zoom"] > settings["map_max_zoom"])):
            out.append(_finding("E-SL-VALUE", node_id,
                                '%s "map_zoom" is outside "map_min_zoom" and "map_max_zoom".' % block_type))
        if is_set("map_center_lat") != is_set("map_center_lng"):
            out.append(_finding("E-SL-VALUE", node_id,
                                '%s "map_center_lat" and "map_center_lng" go together: set both or '
                                "neither." % block_type))

        # What the Clear rule in check() needs: where Clear is hidden, and every filter that
        # starts with a value, with the devices where visitors cannot see it.
        if block_type == "crecs_search_filter_clear":
            state["clear_hidden"] = list(hidden)
            return
        if not block["within"]:
            return
        starts = any(is_set(name) for name in ("start_text", "start_checked", "start_min", "start_max"))
        for choice in ("for_sale", "for_lease"):
            if on("start_" + choice):
                starts = True
                # A choice that starts checked but is hidden can only be cleared by Clear.
                if on(choice + "_option_hide"):
                    hidden = ["desktop", "tablet", "mobile"]
        if starts and hidden:
            state["starts"].append({"node": node_id, "label": block["label"], "devices": list(hidden)})


# ---------------------------------------------------------------------------
# value helpers, as the plugin's
# ---------------------------------------------------------------------------


def is_unset(spec, value):
    """An empty value means "leave the page as it is", and is always acceptable."""
    if value is None or value == "":
        return True
    kind = spec["type"]
    # An empty list leaves the list as the site has it, and an empty choice of parts the
    # card or the popup as the page has it; PHP decodes [] and {} alike.
    if kind in ("list", "fields") and isinstance(value, (list, dict)) and not value:
        return True
    if kind == "slider" and isinstance(value, dict) and value.get("size") == "":
        return True
    if kind == "dimensions":
        if isinstance(value, list):
            return True  # PHP reads a list as an array with no sides set
        if isinstance(value, dict):
            for side in SIDES:
                if value.get(side) is not None and value.get(side) != "":
                    return False
            return True
    return False


def is_color(value):
    if not isinstance(value, str):
        return False
    if value == "transparent" or _HEX.match(value):
        return True
    return _RGB.match(value) is not None


def is_number(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    return isinstance(value, str) and _NUMBER.match(value) is not None


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def _php_trim(value):
    """PHP's trim(): these six characters only, not every Unicode space."""
    return value.strip(" \t\n\r\x00\x0b")


def name_key(name):
    """A name as the page compares it: trimmed, ASCII letters lowercased.

    The checkboxes' values are the site's names lowercased by the browser, and a name that
    differs only in case or surrounding spaces is the same name.
    """
    return _php_trim(str(name)).translate(_ASCII_LOWER)


def php_list(value):
    """The items of a value PHP would take for a list, or None.

    PHP decodes a JSON object whose keys are "0", "1"… in that order into the same array
    as the JSON list, so the plugin accepts it as one.
    """
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict) and list(value) == [str(i) for i in range(len(value))]:
        return list(value.values())
    return None


def _is_utf8(value):
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _strict_in(value, options):
    return isinstance(value, str) and value in options


def _bounds(spec, unit):
    high = min(100, spec["max"]) if unit in ("%", "vh") else spec["max"]
    low = min(10, spec["min"]) if unit == "vh" else spec["min"]
    return low, high


def _in_range(value, spec, unit):
    if not is_number(value):
        return False
    low, high = _bounds(spec, unit)
    return low <= float(value) <= high


def _range_text(spec, unit):
    low, high = _bounds(spec, unit)
    return "must be a number from %s to %s%s" % (_num(low), _num(high), unit)


def _units(spec):
    return ", ".join('"" (no unit)' if u == "" else '"%s"' % u for u in spec["units"])


def _num(value):
    """A number as the plugin prints it: at most three decimals, no trailing zeros."""
    out = ("%.3f" % float(value)).rstrip("0").rstrip(".")
    return "0" if out == "-0" else out


def _php_string(value):
    """(string) $value, for the one message that prints a value of any type."""
    if value is True:
        return "1"
    if value is False or value is None:
        return ""
    if isinstance(value, float):
        return repr(value).rstrip("0").rstrip(".") if value != int(value) else str(int(value))
    if isinstance(value, (list, dict)):
        return "Array"
    return str(value)


def _values(container):
    if isinstance(container, dict):
        return list(container.values())
    return list(container) if isinstance(container, list) else []


def _items(container):
    if isinstance(container, dict):
        return list(container.items())
    if isinstance(container, list):
        return [(str(i), v) for i, v in enumerate(container)]
    return []


def _finding(code, node, message):
    return {"level": "error", "code": code, "node": node, "message": message}


def blocking(findings):
    return any(f.get("level") == "error" for f in findings)


# ---------------------------------------------------------------------------
# the tree
# ---------------------------------------------------------------------------


def walk(document):
    """Yield (node, parent_list, index, depth, ancestors) for every block, in order."""
    def go(nodes, depth, ancestors):
        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            yield node, nodes, index, depth, ancestors
            elements = node.get("elements")
            if isinstance(elements, list) and elements:
                yield from go(elements, depth + 1, ancestors + [node])
    content = document.get("content") if isinstance(document, dict) else None
    if isinstance(content, list):
        yield from go(content, 0, [])


def find(document, node_id):
    """(node, parent_list, index, ancestors) for a block id, or raise."""
    for node, parent, index, _depth, ancestors in walk(document):
        if node.get("id") == node_id:
            return node, parent, index, ancestors
    raise SearchLayoutError("there is no block with the id %s in this layout" % node_id)


def new_id(document, rng=None):
    """A fresh block id: eight hex digits no block uses yet."""
    used = {node.get("id") for node, *_ in walk(document)}
    rng = rng or random.SystemRandom()
    while True:
        candidate = "%08x" % rng.getrandbits(32)
        if candidate not in used and not candidate.isdigit():
            return candidate


def normalise(document):
    """Give every block the shape the plugin stores.

    The plugin encodes an empty settings map as `[]`, PHP having no empty object, and the
    revision hash is taken over that encoding. Keeping `[]` here keeps the hash the skill
    computes equal to the one the site reports.
    """
    for node, *_ in walk(document):
        if isinstance(node.get("settings"), dict) and not node["settings"]:
            node["settings"] = []
        if node.get("elements") is None:
            node["elements"] = []
    return document


def settings_of(node):
    """A node's settings as a dict, whatever encoding it arrived in."""
    settings = node.get("settings")
    if isinstance(settings, dict):
        return settings
    node["settings"] = {}
    return node["settings"]
