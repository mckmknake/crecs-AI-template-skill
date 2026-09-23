"""Dynamic-tag bindings.

Elementor stores a dynamic tag inside the host control's ``__dynamic__`` map:

    "__dynamic__": {
      "title": "[elementor-tag id=\\"c9ca4f5\\" name=\\"crecs-property\\"
                 settings=\\"%7B%22param_name%22%3A%22property_name%22%7D\\"]"
    }

Reading that with one regex would conflate three different failures — a string that
is not a shortcode, a payload that will not decode, and a payload that decodes to
the wrong shape. So the parse is done in stages: find the shortcode, scan its
attributes, URL-decode ``settings``, JSON-parse it, then check it is an object.
Each stage reports its own error.
"""

import json
import re
import secrets
import urllib.parse

_TAG_OPEN = "[elementor-tag"
_ID_SHAPE = re.compile(r"^[0-9a-f]{7,8}$")
# Attribute scanner: name = "value" | 'value' | bare. Deliberately only used to walk
# the attribute list, not to interpret the payload.
_ATTR = re.compile(
    r"""([A-Za-z_][A-Za-z0-9_-]*)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s\]]+))"""
)


class Tag:
    """One parsed dynamic tag. ``error`` is None when every stage succeeded."""

    __slots__ = ("raw", "name", "instance_id", "settings", "error")

    def __init__(self, raw, name=None, instance_id=None, settings=None, error=None):
        self.raw = raw
        self.name = name
        self.instance_id = instance_id
        self.settings = settings if settings is not None else {}
        self.error = error

    def __repr__(self):  # pragma: no cover - debugging aid
        return "Tag(name=%r, settings=%r, error=%r)" % (
            self.name, self.settings, self.error
        )


class Binding:
    """A tag attached to a specific control of a specific element."""

    __slots__ = ("control", "tag", "error")

    def __init__(self, control, tag, error=None):
        self.control = control
        self.tag = tag
        self.error = error if error is not None else (tag.error if tag else None)


def parse_tag(raw):
    """Parse one ``[elementor-tag ...]`` shortcode into a :class:`Tag`."""
    if not isinstance(raw, str):
        return Tag(raw, error="not an elementor-tag shortcode: expected a string, got %s"
                              % type(raw).__name__)

    text = raw.strip()
    if not text.startswith(_TAG_OPEN):
        return Tag(raw, error="not an elementor-tag shortcode: does not start with "
                              "'[elementor-tag'")
    if not text.endswith("]"):
        return Tag(raw, error="unterminated elementor-tag shortcode: no closing ']'")

    inner = text[len(_TAG_OPEN):-1]
    attrs = {}
    for match in _ATTR.finditer(inner):
        key = match.group(1)
        value = match.group(2)
        if value is None:
            value = match.group(3)
        if value is None:
            value = match.group(4)
        attrs[key] = value

    name = attrs.get("name")
    if not name:
        return Tag(raw, error="elementor-tag has no 'name' attribute, so the tag "
                              "cannot be identified")

    instance_id = attrs.get("id")
    if instance_id is not None and not _ID_SHAPE.match(instance_id):
        return Tag(raw, name=name, instance_id=instance_id,
                   error="elementor-tag 'id' attribute %r is not 7-8 lowercase hex "
                         "characters" % instance_id)

    if "settings" not in attrs:
        return Tag(raw, name=name, instance_id=instance_id, settings={})

    encoded = attrs["settings"]
    try:
        decoded = urllib.parse.unquote(encoded)
    except Exception as exc:  # pragma: no cover - unquote is very tolerant
        return Tag(raw, name=name, instance_id=instance_id,
                   error="could not URL-decode the settings payload: %s" % exc)

    try:
        payload = json.loads(decoded)
    except ValueError as exc:
        return Tag(raw, name=name, instance_id=instance_id,
                   error="settings payload is not valid JSON after URL-decoding "
                         "(%s); decoded value was %r" % (exc, decoded[:80]))

    if not isinstance(payload, dict):
        return Tag(raw, name=name, instance_id=instance_id,
                   error="settings payload decoded to %s, but Elementor stores a JSON "
                         "object" % type(payload).__name__)

    return Tag(raw, name=name, instance_id=instance_id, settings=payload)


def build_tag(name, settings, instance_id=None):
    """Serialise a tag the way Elementor does."""
    if not isinstance(name, str) or not name:
        raise ValueError("tag name must be a non-empty string")
    if not isinstance(settings, dict):
        raise ValueError("tag settings must be a JSON object (a dict), got %s"
                         % type(settings).__name__)
    if instance_id is None:
        instance_id = secrets.token_hex(4)[:7]
    if not _ID_SHAPE.match(instance_id):
        raise ValueError("instance_id must be 7-8 lowercase hex characters")

    payload = json.dumps(settings, separators=(",", ":"), sort_keys=True)
    encoded = urllib.parse.quote(payload, safe="")
    return '[elementor-tag id="%s" name="%s" settings="%s"]' % (
        instance_id, name, encoded
    )


def read_element_bindings(settings):
    """Read every binding declared in one element's settings."""
    if not isinstance(settings, dict):
        return []
    dynamic = settings.get("__dynamic__")
    if dynamic is None:
        return []
    if dynamic == []:
        # Elementor's own marker for "no bindings left on this element". PHP has one
        # array type, so an empty map comes back from any WordPress round trip as `[]`
        # rather than `{}`. Calling that corrupt refused documents the site itself had
        # just produced.
        return []
    if not isinstance(dynamic, dict):
        return [Binding(
            "__dynamic__",
            Tag(dynamic, error="__dynamic__ must be an object mapping control name to "
                               "shortcode, got %s" % type(dynamic).__name__),
        )]
    out = []
    for control in sorted(dynamic):
        out.append(Binding(control, parse_tag(dynamic[control])))
    return out


def set_element_binding(settings, control, name, payload, instance_id=None):
    """Attach a binding, creating ``__dynamic__`` if needed. Mutates ``settings``."""
    dynamic = settings.get("__dynamic__")
    if not isinstance(dynamic, dict):
        dynamic = {}
    dynamic[control] = build_tag(name, payload, instance_id=instance_id)
    settings["__dynamic__"] = dynamic
    return settings["__dynamic__"][control]


def clear_element_binding(settings, control):
    """Detach a binding. Returns True when something was removed.

    An empty ``__dynamic__`` map is deleted rather than left behind, because
    Elementor writes the key only when at least one binding exists.
    """
    dynamic = settings.get("__dynamic__")
    if not isinstance(dynamic, dict) or control not in dynamic:
        return False
    del dynamic[control]
    if not dynamic:
        del settings["__dynamic__"]
    return True
