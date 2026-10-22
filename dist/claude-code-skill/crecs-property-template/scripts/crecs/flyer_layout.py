"""The property flyer's layout document: vocabulary, checks and tree helpers.

The flyer's designed pages are drawn by the plugin from a layout document — a tree of
blocks in Elementor's shape — that says what each page holds, where, and how it looks.
CRE Cloud prints them to PDF. See references/flyer/FLYER-LAYOUT.md.

Everything this module knows about blocks and controls comes from
references/flyer/flyer-layout.json, which the plugin generates from its own registry.
Nothing here is hand-maintained: if a block or a control is missing, the answer is to
regenerate that file from the plugin, never to add it here.

`problem()`, `check()` and `option()` are ports of the plugin's
Crecs_Flyer_Layout_Controls::problem(), Crecs_Flyer_Layout_Validate::check() and
Crecs_Flyer_Layout::option(), and must agree with them word for word; `is_unset()`,
`normalise()` and `extent()` port the controls' helpers of the same names, which the
checks rest on (a fixed height against the padding and border inside it, a page's room
between the bands, a row's columns and gaps against the narrowest page).
tests/test_flyer.py holds them to the plugin's own verdicts in
tests/fixtures/flyer-vectors.json. The plugin checks every design again whatever this
module concluded; checking here is what lets the assistant say what is wrong before
anything is sent.

The plugin reads a document as PHP decodes JSON: an object and a list are both arrays,
and an object whose keys are "0", "1"… in that order is a list. The helpers below
(`php_list`, `_items`) read Python's dicts and lists the same way.
"""

import json
import math
import os
import random
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(_HERE))  # skill root
REFERENCE = os.path.join(_PACKAGE_ROOT, "references", "flyer", "flyer-layout.json")

TYPE = "crecs-flyer-layout"
VERSION = 1
SIDES = ("top", "right", "bottom", "left")

# PCRE's \s and \d without the u modifier: ASCII only, which Python's are not.
_WS = r"[ \t\n\x0b\x0c\r]*"
_BYTE = _WS + r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})" + _WS
_ALPHA = _WS + r"(?:0|1|0?\.[0-9]{1,3}|1\.0{1,3})" + _WS
# The plugin's patterns carry the D modifier: `$` is the very end, a final line break
# refused. Python's `\Z` is that.
# No #rgba or #rrggbbaa: the flyer printer (wkhtmltopdf 0.11) drops a hex alpha silently.
_HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")
_HEX_ALPHA = re.compile(r"^#([0-9a-fA-F]{4}|[0-9a-fA-F]{8})\Z")
_RGB = re.compile(r"^rgba?\(" + _BYTE + "," + _BYTE + "," + _BYTE + "(?:," + _ALPHA + r")?\)\Z")
_NUMBER = re.compile(r"^-?[0-9]{1,5}(?:\.[0-9]{1,3})?\Z")
_WHOLE = re.compile(r"^-?[0-9]+\Z")
_CONTROL_CHAR = re.compile(r"[\x00-\x1f\x7f]")
_CONTROL_CHAR_BUT_LF = re.compile(r"[\x00-\x09\x0b-\x1f\x7f]")
_ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


class FlyerLayoutError(Exception):
    """A document or an edit this module refuses."""


class Vocabulary:
    """The plugin's registry, as references/flyer/flyer-layout.json records it."""

    def __init__(self, data):
        self.data = data
        self.blocks = data["blocks"]
        self.fonts = data["fonts"]
        self.limits = data["limits"]
        self.page_boxes = data["page_boxes"]
        self.codes = data["codes"]
        self.root = data["root"]
        self.properties = data["properties"]
        self.document_keys = data["document"]["keys"]
        self.node_keys = data["node_keys"]
        self.value_keys = data["value_keys"]
        self.builtins = data.get("builtins") or {}
        if not isinstance(self.builtins, dict):
            self.builtins = {}
        pattern = self.limits["id_pattern"]
        flags = self.limits.get("id_flags", "")
        # ASCII case folding only, as PCRE without the u modifier: in Unicode mode
        # Python would also take the Kelvin sign for a k.
        body = pattern[1:] if pattern.startswith("^") else pattern
        body = body[:-1] if body.endswith("$") else body
        self._id = re.compile(body, re.ASCII | (re.IGNORECASE if "i" in flags else 0))

    @classmethod
    def load(cls, path=REFERENCE):
        try:
            with open(path, encoding="utf-8") as fh:
                return cls(json.load(fh))
        except (OSError, ValueError, KeyError) as exc:
            raise FlyerLayoutError("the flyer layout reference could not be read (%s): %s"
                                   % (path, exc))

    def block(self, block_type):
        return self.blocks.get(block_type) if isinstance(block_type, str) else None

    def controls(self, block_type):
        block = self.block(block_type)
        return block["controls"] if block else {}

    def label(self, block_type):
        block = self.block(block_type)
        return block["label"] if block else str(block_type)

    def is_id(self, value):
        return isinstance(value, str) and self._id.fullmatch(value) is not None

    def orientations(self):
        return list(self.page_boxes)

    def resolve(self, name):
        """A block's key from its key, its key without `crecs_flyer_`, its part or its label."""
        if not isinstance(name, str):
            return None
        wanted = name.strip()
        if wanted in self.blocks:
            return wanted
        folded = wanted.lower().replace("-", "_").replace(" ", "_")
        for key, block in self.blocks.items():
            names = {key, key[len("crecs_flyer_"):] if key.startswith("crecs_flyer_") else key,
                     block["part"].replace("-", "_"), block["label"].lower().replace(" ", "_")}
            if folded in names:
                return key
        return None

    # -- values -------------------------------------------------------------------

    def problem(self, spec, value):
        """None when `value` is acceptable for the control `spec`, otherwise why not."""
        if self.is_unset(spec, value):
            return None
        kind = spec.get("type", "")
        if kind == "color":
            if is_color(value):
                return None
            rgba = _hex_alpha_as_rgba(value)
            if rgba is not None:
                return "has its transparency written in hex, which the flyer printer ignores: write it as " + rgba
            return "is not a colour (#rgb, #rrggbb, rgb(), rgba() or transparent)"
        if kind == "select":
            return None if _strict_in(value, spec["options"]) else \
                "must be one of: " + _quoted(spec["options"])
        if kind == "font":
            return None if _strict_in(value, list(self.fonts)) else \
                "must be one of the fonts the flyer printer has: " + ", ".join(self.fonts)
        if kind == "number":
            if spec.get("auto") and value == "auto":
                return None
            ok = _is_int(value) and spec["min"] <= value <= spec["max"]
            return None if ok else _number_text(spec)
        if kind == "media":
            # Only the number: whether it is an image of the site is the preview's to say.
            ok = _is_int(value) and 1 <= value <= self.limits["media_max"]
            return None if ok else (
                "must be the number of an image in the media library, a whole number from 1 to %d"
                % self.limits["media_max"])
        if kind == "fields":
            return _fields_problem(spec, value)
        if kind == "text":
            return _text_problem(spec, value, self.limits["text_max"])
        if kind == "slider":
            shape = 'must be {"unit": one of ' + _units(spec) + ', "size": a number}'
            if not isinstance(value, (dict, list)):
                return shape
            extra = _extra_key(value, self.value_keys["slider"])
            if extra is not None:
                return 'may hold only %s, not "%s"' % (_quoted(self.value_keys["slider"]), extra)
            if not isinstance(value, dict) or "unit" not in value \
                    or not _strict_in(value["unit"], spec["units"]):
                return shape
            if self.in_range(value.get("size"), spec, value["unit"]):
                return None
            return _range_text(spec, value["unit"])
        if kind == "dimensions":
            shape = 'must be {"unit": one of ' + _units(spec) + ', "top", "right", "bottom", "left": numbers}'
            if not isinstance(value, (dict, list)):
                return shape
            extra = _extra_key(value, self.value_keys["dimensions"])
            if extra is not None:
                return 'may hold only %s, not "%s"' % (_quoted(self.value_keys["dimensions"]), extra)
            if not isinstance(value, dict) or "unit" not in value \
                    or not _strict_in(value["unit"], spec["units"]):
                return shape
            for side in SIDES:
                if side not in value or not self.in_range(value[side], spec, value["unit"]):
                    return "'%s' %s" % (side, _range_text(spec, value["unit"]))
            if value.get("isLinked") is not None and not isinstance(value["isLinked"], bool):
                return "'isLinked' must be true or false"
            return None
        return "has a type this plugin does not know"

    def is_unset(self, spec, value):
        """An empty value means "the block's default", and is always acceptable; a size or
        four sides holding any other key are not empty, so problem() refuses them."""
        if value is None or (isinstance(value, str) and value == ""):
            return True
        kind = spec.get("type", "")
        # PHP decodes [] and {} alike, to the empty array.
        if kind == "fields" and isinstance(value, (list, dict)) and not value:
            return True
        if kind == "slider" and isinstance(value, dict) \
                and _extra_key(value, self.value_keys["slider"]) is None \
                and "size" in value and isinstance(value["size"], str) and value["size"] == "":
            return True
        if kind == "dimensions" and isinstance(value, (dict, list)) \
                and _extra_key(value, self.value_keys["dimensions"]) is None:
            if isinstance(value, list):
                return True  # only the empty list has no key: PHP's empty array
            for side in SIDES:
                if value.get(side) is not None and not (isinstance(value[side], str) and value[side] == ""):
                    return False
            return True
        return False

    def is_number(self, value):
        """A plain decimal: an int, or a finite float with at most three decimals, below
        `number_limit` in magnitude; or its text (at most 5 digits and 3 decimals)."""
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return abs(value) < self.limits["number_limit"]
        if isinstance(value, float):
            return math.isfinite(value) and abs(value) < self.limits["number_limit"] \
                and abs(value * 1000 - round(value * 1000)) < 1e-6
        return isinstance(value, str) and _NUMBER.match(value) is not None

    def in_range(self, value, spec, unit):
        if not self.is_number(value):
            return False
        return spec["min"] <= float(value) <= _high(spec, unit)

    def normalise(self, spec, value):
        """An accepted, set value in its plain form, as the plugin's
        Crecs_Flyer_Layout_Controls::normalise(): numbers in a size or a side as int or
        float, never text; a size as exactly {unit, size}; four sides as exactly {unit,
        top, right, bottom, left}; a choice of parts as a list. Anything else as it is."""
        kind = spec.get("type", "")
        if kind == "slider":
            return {"unit": value["unit"], "size": _to_number(value["size"])}
        if kind == "dimensions":
            out = {"unit": value["unit"]}
            for side in SIDES:
                out[side] = _to_number(value[side])
            return out
        if kind == "fields":
            return php_list(value)
        return value

    def extent(self, settings, target):
        """A target's padding plus border width in CSS px, from a node's settings: `h`
        across (left + right), `v` down (top + bottom). What is unset, or refused, counts
        as nothing. Crecs_Flyer_Layout_Controls::extent()."""
        h, v = 0.0, 0.0
        if isinstance(settings, (dict, list)) and isinstance(target, str):
            values = dict(_items(settings))
            for prop in ("padding", "border_width"):
                name = target + "_" + prop
                if name not in values:
                    continue
                spec = self.properties[prop]
                if self.is_unset(spec, values[name]) or self.problem(spec, values[name]) is not None:
                    continue
                sides = self.normalise(spec, values[name])
                h += sides["left"] + sides["right"]
                v += sides["top"] + sides["bottom"]
        return {"h": float(h), "v": float(v)}

    def smallest_page(self, axis):
        """(orientation, size) of the page box smallest along an axis: 0 the width, 1 the
        height. The first in the reference's order wins a tie, as in the plugin."""
        best = None
        for orientation, box in self.page_boxes.items():
            if best is None or box[axis] < best[1]:
                best = (orientation, box[axis])
        return best

    def option(self, node, name):
        """A node's setting as the renderer reads it: the value when it is set and
        acceptable, otherwise the control's default, otherwise None."""
        if not isinstance(node, dict) or not isinstance(node.get("widgetType"), str) \
                or not isinstance(name, str):
            return None
        controls = self.controls(node["widgetType"])
        if name not in controls:
            return None
        spec = controls[name]
        settings = node.get("settings")
        value = settings[name] if isinstance(settings, dict) and name in settings else None
        if self.is_unset(spec, value) or self.problem(spec, value) is not None:
            return spec.get("default")
        return self.normalise(spec, value)

    # -- documents ----------------------------------------------------------------

    def check(self, document):
        """Every finding for a document, as the plugin reports them."""
        out = []
        if not isinstance(document, dict) or document.get("type") != TYPE \
                or not (_is_int(document.get("version")) and document["version"] == VERSION) \
                or document.get("content") is None or php_list(document["content"]) is None:
            out.append(_finding(
                "E-FL-SHAPE", None,
                'Not a flyer layout document: it needs "type": "%s", "version": %d and a '
                '"content" list.' % (TYPE, VERSION)))
            return out
        extra = [key for key in _keys(document) if key not in self.document_keys]
        if extra:
            out.append(_finding(
                "E-FL-SHAPE", None,
                "The document has %s, %s no flyer layout document has: it holds only %s."
                % (_quoted(extra), "a key" if len(extra) == 1 else "keys",
                   _quoted(self.document_keys, " and "))))
            return out
        if "title" in document and not self.is_title(document["title"]):
            out.append(_finding(
                "E-FL-SHAPE", None,
                'The document\'s "title" must be one line of at most %d characters.'
                % self.limits["title_max"]))
            return out

        content = php_list(document["content"])
        first = content[0] if len(content) == 1 else None
        if len(content) != 1 or not isinstance(first, dict) or first.get("widgetType") != self.root:
            out.append(_finding(
                "E-FL-ROOT", None,
                "The content must be exactly one %s block, with everything else inside it."
                % self.root))

        state = {"ids": set(), "counts": {}, "nodes": 0, "depth": 0}
        self._walk(content, None, 0, state, out)
        self._check_room(content, out)

        for block_type, block in self.blocks.items():
            n = state["counts"].get(block_type, 0)
            if block["required"] and n == 0:
                out.append(_finding("E-FL-REQUIRED", None, 'The flyer needs the "%s" block (%s).'
                                    % (block["label"], block_type)))
            if block["once"] and n > 1:
                out.append(_finding("E-FL-ONCE", None,
                                    'The "%s" block (%s) appears %d times; it may appear once.'
                                    % (block["label"], block_type, n)))
            count = block.get("count")
            if count and (n < count[0] or n > count[1]):
                out.append(_finding("E-FL-PAGES", None,
                                    "The flyer has %d %s blocks (%s); it needs %d to %d."
                                    % (n, block["label"].translate(_ASCII_LOWER), block_type,
                                       count[0], count[1])))
            # A block's registry `max` (today only the Logo block's: limits.max_logos). The
            # label is printed as it is, not lowercased: the plugin words it so.
            most = block.get("max")
            if most is not None and n > most:
                out.append(_finding(
                    "E-FL-LIMIT", None,
                    "The flyer has %d %s blocks (%s); it may have at most %d, because each one "
                    "carries a whole image that every page of its band prints again, and so does "
                    "each attachment frame." % (n, block["label"], block_type, most)))

        if state["nodes"] > self.limits["max_nodes"] or state["depth"] > self.limits["max_depth"]:
            out.append(_finding(
                "E-FL-LIMIT", None,
                "The document has %d blocks nested %d deep; a flyer may have at most %d blocks, "
                "%d deep." % (state["nodes"], state["depth"], self.limits["max_nodes"],
                              self.limits["max_depth"])))
        return out

    def is_title(self, value):
        """A document title: one line of at most `title_max` characters."""
        return isinstance(value, str) and _is_utf8(value) and not _CONTROL_CHAR.search(value) \
            and len(value) <= self.limits["title_max"]

    def _walk(self, nodes, parent, level, state, out):
        """`parent`: the parent's block type, None at the top; `level`: how deep it is."""
        state["depth"] = max(state["depth"], level + 1)
        for node in nodes:
            state["nodes"] += 1
            if not isinstance(node, dict) \
                    or any(node.get(key) is None for key in ("id", "elType", "widgetType", "settings", "elements")) \
                    or not isinstance(node["elType"], str) or not isinstance(node["widgetType"], str) \
                    or not isinstance(node["settings"], (dict, list)) or php_list(node["elements"]) is None:
                node_id = node.get("id") if isinstance(node, dict) and isinstance(node.get("id"), str) else None
                out.append(_finding("E-FL-NODE", node_id,
                                    'A block must have an "id", an "elType", a "widgetType", a '
                                    '"settings" object and an "elements" list.'))
                continue
            # Its five keys and nothing else; the rest of the block is still checked.
            extra = [key for key in _keys(node) if key not in self.node_keys]
            if extra:
                out.append(_finding("E-FL-NODE", node["id"] if isinstance(node["id"], str) else None,
                                    "The block has %s, %s no block has: a block holds only %s."
                                    % (_quoted(extra), "a key" if len(extra) == 1 else "keys",
                                       _quoted(self.node_keys, " and "))))

            node_id = node["id"]
            if not self.is_id(node_id):
                out.append(_finding("E-FL-ID", None, "A block id must be 4 to 16 letters or digits."))
                node_id = None
            elif node_id in state["ids"]:
                out.append(_finding("E-FL-ID", node_id, "The id %s is used by more than one block." % node_id))
            else:
                state["ids"].add(node_id)

            block_type = node["widgetType"]
            block = self.blocks.get(block_type)
            if block is None:
                out.append(_finding("E-FL-BLOCK", node_id, 'There is no "%s" block in a flyer.' % block_type))
                continue
            state["counts"][block_type] = state["counts"].get(block_type, 0) + 1

            if block["kind"] != node["elType"]:
                out.append(_finding("E-FL-ELTYPE", node_id,
                                    '%s is a %s, so its "elType" must be "%s", not "%s".'
                                    % (block_type, block["kind"], block["kind"], node["elType"])))
            elements = php_list(node["elements"])
            if block["kind"] == "widget" and elements:
                out.append(_finding("E-FL-CHILDREN", node_id, "%s cannot hold other blocks." % block_type))
            if block_type == self.root and parent is not None:
                out.append(_finding("E-FL-ROOT", node_id,
                                    "The %s block can only be the document's root." % self.root))
            elif parent is not None and block["within"] and parent not in block["within"]:
                out.append(_finding(
                    "E-FL-WITHIN", node_id,
                    'The "%s" block (%s) cannot sit in %s; it goes directly in %s.'
                    % (block["label"], block_type, parent, " or ".join(block["within"]))))

            controls = block["controls"]
            for name, value in _items(node["settings"]):
                if name not in controls:
                    out.append(_finding("E-FL-SETTING", node_id, '%s has no "%s" setting.' % (block_type, name)))
                    continue
                problem = self.problem(controls[name], value)
                if problem is not None:
                    code = "E-FL-FONT" if controls[name]["type"] == "font" else "E-FL-VALUE"
                    out.append(_finding(code, node_id, '%s "%s" %s.' % (block_type, name, problem)))

            self._check_together(block_type, node_id, node, elements, out)

            if elements:
                self._walk(elements, block_type, level + 1, state, out)

    def _check_together(self, block_type, node_id, node, elements, out):
        """Rules between settings: a fixed height must keep room once the padding and border
        it holds come out of it; a row's columns must fit in it, and in the narrowest page
        with its gaps; a logo's image goes with its source; a map's boundaries need a
        satellite or hybrid map. A setting that is itself refused, or not set, counts as its
        default (padding and border as none)."""
        self._check_heights(block_type, node_id, node, out)

        if block_type == "crecs_flyer_row":
            total, unset, count = 0, 0, 0
            for child in elements:
                if not isinstance(child, dict) or child.get("widgetType") != "crecs_flyer_column":
                    continue
                count += 1
                width = self.option(child, "width")
                if width is None:
                    unset += 1
                else:
                    total += width
            least = self.limits["min_column"]
            if total + least * unset > 100:
                if unset:
                    message = ('The columns of this row with a "width" add up to %d%%, leaving less '
                               "than %d%% to each of the %d without one; a row is 100%% wide."
                               % (total, least, unset))
                else:
                    message = "The columns of this row add up to %d%% wide; a row is 100%% wide." % total
                out.append(_finding("E-FL-VALUE", node_id, message))
            # (columns - 1) x gap + columns x min_column_px must fit in the narrowest page.
            gap = self.option(node, "gap") or 0
            least_px = self.limits["min_column_px"]
            need = count * least_px + max(0, count - 1) * gap
            narrow = self.smallest_page(0)
            if need > narrow[1]:
                out.append(_finding(
                    "E-FL-VALUE", node_id,
                    "The %d columns of this row, at least %d px each, and the %d px gaps between them "
                    "need %d px, more than a %s page's %d px width."
                    % (count, least_px, gap, need, narrow[0], narrow[1])))
            return

        if block_type == "crecs_flyer_logo":
            media = self.option(node, "media_id")
            if self.option(node, "source") == "media":
                if media is None:
                    out.append(_finding(
                        "E-FL-VALUE", node_id,
                        '%s "source" is "media", so it needs "media_id", the number of an image in '
                        "the media library." % block_type))
            elif media is not None:
                # The logo shows what its source says (the site logo when the source is unset or
                # refused): the plugin words the refusal by which one that is.
                shows = {"company_logo": "the company logo kept in CRE Cloud",
                         "flyer_logo": "the flyer logo kept in CRE Cloud"}
                out.append(_finding(
                    "E-FL-VALUE", node_id,
                    '%s "media_id" is used only when "source" is "media"; the logo now shows %s.'
                    % (block_type, shows.get(self.option(node, "source"), "the site logo"))))
            return

        # CRE Cloud draws a property's boundaries only on an aerial picture, and refuses a
        # road map that asks for them, so the document must not (the plugin's own rule).
        if block_type == "crecs_flyer_map":
            kind = self.option(node, "map_type")
            if self.option(node, "boundaries") == "on" and kind not in ("satellite", "hybrid"):
                out.append(_finding(
                    "E-FL-VALUE", node_id,
                    '%s "boundaries" is "on", which only a satellite or hybrid map can show; this '
                    'map is a %s map (its "map_type"), so set "map_type" to "satellite" or '
                    '"hybrid", or "boundaries" to "off".' % (block_type, kind)))

    def _check_heights(self, block_type, node_id, node, out):
        """Each fixed height (an option naming in `sizes` the part it sizes) keeps at least
        `min_content` px once that part's padding and border, top and bottom, come out of
        it. A row of automatic height has nothing to keep."""
        least = self.limits["min_content"]
        for name, spec in self.controls(block_type).items():
            if spec.get("group") != "option" or "sizes" not in spec:
                continue
            height = self.option(node, name)
            if not _is_int(height):
                continue
            v = self.extent(node["settings"], spec["sizes"])["v"]
            if v > 0 and height - v < least:
                out.append(_finding(
                    "E-FL-VALUE", node_id,
                    '%s "%s" leaves less than %d px for what the block holds once the padding and '
                    'border of "%s" (%s px top and bottom) come out of it: %s px short.'
                    % (block_type, name, least, spec["sizes"], _num(v), _num(least - (height - v)))))

    def _check_room(self, content, out):
        """Every page's body keeps `min_body` px of the shortest page box (landscape) once
        the root's padding and border, the header's and the footer's heights, and the page
        body's padding and border come out of it. A band's own padding and border are not
        added: a fixed height is the outer size of the part it sizes, so they are inside the
        band's height (`_check_heights` holds them to `min_content`). Both bands count on
        every page: the frames around attachments print both, in both orientations."""
        root = content[0] if len(content) == 1 else None
        if not isinstance(root, dict) or root.get("widgetType") != self.root \
                or root.get("elements") is None or php_list(root["elements"]) is None:
            return
        bands = {"crecs_flyer_header": None, "crecs_flyer_footer": None}
        pages = []
        for child in php_list(root["elements"]):
            if not isinstance(child, dict) or not isinstance(child.get("widgetType"), str):
                continue
            if child["widgetType"] in bands and bands[child["widgetType"]] is None:
                bands[child["widgetType"]] = child
            elif child["widgetType"] == "crecs_flyer_page":
                pages.append(child)

        taken = self.extent(root.get("settings"), "page")["v"]
        for band in bands.values():
            if band is not None:
                taken += int(self.option(band, "height"))
        short = self.smallest_page(1)
        least = self.limits["min_body"]
        for page in pages:
            total = taken + self.extent(page.get("settings"), "body")["v"]
            if short[1] - total < least:
                out.append(_finding(
                    "E-FL-VALUE", page.get("id") if self.is_id(page.get("id")) else None,
                    "The flyer's padding and border, the header and footer heights and this page's "
                    "body padding and border take %s px of the %d px a %s page is high, leaving less "
                    "than the %d px a page's body needs (a band's own padding and border are inside "
                    "its height; attachments are framed in both orientations, so every flyer must "
                    "fit a %s page)." % (_num(total), short[1], short[0], least, short[0])))


# ---------------------------------------------------------------------------
# value helpers, as the plugin's
# ---------------------------------------------------------------------------


def is_color(value):
    """#rgb or #rrggbb, rgb(), rgba() or transparent; never a hex colour with alpha."""
    if not isinstance(value, str):
        return False
    if value == "transparent" or _HEX.match(value):
        return True
    return _RGB.match(value) is not None


def _hex_alpha_as_rgba(value):
    """#rgba or #rrggbbaa as the rgba() that means the same, alpha to three decimals."""
    match = _HEX_ALPHA.match(value) if isinstance(value, str) else None
    if match is None:
        return None
    digits = match.group(1)
    if len(digits) == 4:
        digits = "".join(c * 2 for c in digits)
    r, g, b, a = (int(digits[i:i + 2], 16) for i in range(0, 8, 2))
    return "rgba(%d, %d, %d, %s)" % (r, g, b, _num(a / 255))


def _keys(value):
    """An array's keys as PHP's (string) $key gives them: a list's are its indexes."""
    if isinstance(value, dict):
        return [str(key) for key in value]
    if isinstance(value, list):
        return [str(index) for index in range(len(value))]
    return []


def _extra_key(value, keys):
    """The first key of an array that is not one of `keys`, or None."""
    for key in _keys(value):
        if key not in keys:
            return key
    return None


def _to_number(value):
    """A number the checks accept, as an int when its text is whole, else as it is or a float."""
    if isinstance(value, str):
        return int(value) if _WHOLE.match(value) else float(value)
    return value


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_utf8(value):
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _strict_in(value, options):
    return isinstance(value, str) and value in options


def _quoted(values, last=", "):
    """"a", "b", "c" — or "a", "b" and "c" with `last` " and "."""
    quoted = ['"%s"' % v for v in values]
    if len(quoted) < 2:
        return "".join(quoted)
    return ", ".join(quoted[:-1]) + last + quoted[-1]


def _number_text(spec):
    unit = spec.get("unit")
    suffix = "" if unit is None else (" (%)" if unit == "%" else " (%s)" % unit)
    text = "must be a whole number from %d to %d%s" % (spec["min"], spec["max"], suffix)
    return text + ', or "auto"' if spec.get("auto") else text


def _fields_problem(spec, value):
    """Why a choice of parts is not acceptable, or None. Each part once, in its order."""
    parts = ", ".join(spec["options"])
    items = php_list(value)
    if items is None or not items:
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
    return None


def _text_problem(spec, value, text_max):
    """Why a text is not acceptable, or None: no control character but the line break
    where the slot is multiline, at most `max` characters."""
    most = spec.get("max", text_max)
    multiline = bool(spec.get("multiline"))
    if multiline:
        shape = "must be text of at most %d characters, with line breaks written \\n" % most
    else:
        shape = "must be one line of at most %d characters" % most
    if not isinstance(value, str) or not _is_utf8(value):
        return shape
    controls = _CONTROL_CHAR_BUT_LF if multiline else _CONTROL_CHAR
    if controls.search(value) or len(value) > most:
        return shape
    return None


def _high(spec, unit):
    return min(100, spec["max"]) if unit == "%" else spec["max"]


def _range_text(spec, unit):
    return "must be a number from %s to %s%s" % (_num(spec["min"]), _num(_high(spec, unit)), unit)


def _units(spec):
    return ", ".join('"" (no unit)' if u == "" else '"%s"' % u for u in spec["units"])


def _num(value):
    """A number as the plugin prints it: at most three decimals, no trailing zeros."""
    out = ("%.3f" % float(value)).rstrip("0").rstrip(".")
    return "0" if out == "-0" else out


def php_list(value):
    """The items of a value PHP would take for a list, or None.

    PHP decodes a JSON object whose keys are "0", "1"… in that order into the same array
    as the JSON list, and {} into the empty one.
    """
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict) and list(value) == [str(i) for i in range(len(value))]:
        return list(value.values())
    return None


def _items(container):
    """(name, value) pairs of a settings array, the names as PHP's (string) $key gives them."""
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
    raise FlyerLayoutError("there is no block with the id %s in this flyer" % node_id)


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

    The plugin encodes an empty settings map as `[]`, PHP having no empty object, and a
    revision hash is taken over that encoding. Keeping `[]` here keeps the hash the skill
    computes equal to the one the site reports.
    """
    content = document.get("content") if isinstance(document, dict) else None
    if isinstance(content, dict) and php_list(content) is not None:
        document["content"] = php_list(content)
    for node, *_ in walk(document):
        if isinstance(node.get("settings"), dict) and not node["settings"]:
            node["settings"] = []
        elements = node.get("elements")
        if elements is None:
            node["elements"] = []
        elif isinstance(elements, dict) and php_list(elements) is not None:
            node["elements"] = php_list(elements)
    return document


def settings_of(node):
    """A node's settings as a dict, whatever encoding it arrived in."""
    settings = node.get("settings")
    if isinstance(settings, dict):
        return settings
    node["settings"] = {}
    return node["settings"]
