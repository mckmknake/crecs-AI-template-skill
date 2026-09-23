"""The Elementor document model.

Two rules the rest of the package depends on:

* **nothing is coerced.** Settings are stored back exactly as they were read, so
  ``""``, ``0``, ``false``, ``null``, ``[]`` and ``{}`` stay distinct, and keys this
  package has never heard of survive untouched.
* **ids are stable.** Editing, moving and re-saving never regenerates an id.
"""

import re
import secrets

ID_SHAPE = re.compile(r"^[0-9a-f]{7,8}$")

ENVELOPE_KEYS = ("content", "page_settings", "version", "title", "type")

CONTAINER_TYPES = ("container",)
_VALID_ELTYPES = ("section", "column", "widget", "container")


class DocumentError(Exception):
    """Raised for anything the caller can fix: a bad id, bad nesting, a missing key."""


class Element:
    """A live view over one raw element dict. Mutating it mutates the document."""

    __slots__ = ("raw",)

    def __init__(self, raw):
        self.raw = raw

    @property
    def id(self):
        return self.raw.get("id")

    @property
    def el_type(self):
        return self.raw.get("elType")

    @property
    def widget_type(self):
        return self.raw.get("widgetType")

    @property
    def settings(self):
        settings = self.raw.get("settings")
        if settings is None:
            settings = {}
            self.raw["settings"] = settings
        if not isinstance(settings, dict):
            raise DocumentError(
                "element %s has a non-object 'settings' (%s); the document is malformed"
                % (self.id, type(settings).__name__)
            )
        return settings

    @property
    def children(self):
        return [Element(c) for c in (self.raw.get("elements") or [])]

    @property
    def kind(self):
        """`section`, `column`, `container`, or the widget's technical name."""
        if self.el_type == "widget":
            return self.widget_type or "(unknown widget)"
        return self.el_type

    def __repr__(self):  # pragma: no cover
        return "Element(%s %s)" % (self.id, self.kind)


class Document:
    """An Elementor page export, with or without its envelope."""

    def __init__(self, payload):
        if isinstance(payload, list):
            self.envelope = None
            self._content = payload
        elif isinstance(payload, dict):
            if "content" not in payload:
                raise DocumentError(
                    "not an Elementor export: no 'content' key. Expected either the "
                    "full envelope {content, page_settings, version, title, type} or a "
                    "bare array of elements."
                )
            if not isinstance(payload["content"], list):
                raise DocumentError(
                    "'content' must be an array of elements, got %s"
                    % type(payload["content"]).__name__
                )
            self.envelope = payload
            self._content = payload["content"]
        else:
            raise DocumentError(
                "not an Elementor export: expected an object or an array, got %s"
                % type(payload).__name__
            )

        for index, raw in enumerate(self._content):
            self._check_shape(raw, "content[%d]" % index)

    # -- shape ---------------------------------------------------------------

    def _check_shape(self, raw, where):
        if not isinstance(raw, dict):
            raise DocumentError("%s is %s, expected an element object"
                                % (where, type(raw).__name__))
        if "elType" not in raw:
            raise DocumentError("%s has no 'elType'; every Elementor element must "
                                "declare one of %s"
                                % (where, ", ".join(_VALID_ELTYPES)))
        children = raw.get("elements")
        if children is not None and not isinstance(children, list):
            raise DocumentError("%s has a non-array 'elements'" % where)
        for index, child in enumerate(children or []):
            self._check_shape(child, "%s/elements[%d]" % (where, index))

    # -- reading -------------------------------------------------------------

    @property
    def content(self):
        return self._content

    @property
    def roots(self):
        return [Element(r) for r in self._content]

    @property
    def export_version(self):
        return self.envelope.get("version") if self.envelope else None

    @property
    def doc_type(self):
        return self.envelope.get("type") if self.envelope else None

    def to_envelope(self):
        """The payload to write back: the envelope if there was one, else the array."""
        if self.envelope is None:
            return self._content
        self.envelope["content"] = self._content
        return self.envelope

    def elements(self):
        out = []

        def walk(raw):
            out.append(Element(raw))
            for child in raw.get("elements") or []:
                walk(child)

        for raw in self._content:
            walk(raw)
        return out

    def widgets(self):
        return [e for e in self.elements() if e.el_type == "widget"]

    def by_id(self, element_id):
        for element in self.elements():
            if element.id == element_id:
                return element
        raise DocumentError(
            "no element with id %r in this document. Run `inspect --tree` to list the "
            "ids." % element_id
        )

    def try_by_id(self, element_id):
        try:
            return self.by_id(element_id)
        except DocumentError:
            return None

    def parent_of(self, element):
        target = element.raw if isinstance(element, Element) else element

        def walk(raw):
            for child in raw.get("elements") or []:
                if child is target:
                    return raw
                found = walk(child)
                if found is not None:
                    return found
            return None

        for raw in self._content:
            if raw is target:
                return None
            found = walk(raw)
            if found is not None:
                return Element(found)
        return None

    def path_of(self, element):
        target = element.raw if isinstance(element, Element) else element
        trail = []

        def walk(raw, prefix):
            label = "%s:%s" % (raw.get("elType"), raw.get("widgetType")) \
                if raw.get("elType") == "widget" else raw.get("elType")
            here = "%s/%s" % (prefix, label)
            if raw is target:
                trail.append(here)
                return True
            for index, child in enumerate(raw.get("elements") or []):
                if walk(child, "%s[%d]" % (here, index)):
                    return True
            return False

        for index, raw in enumerate(self._content):
            if walk(raw, "#%d" % index):
                break
        return trail[0] if trail else "?"

    def ancestors_of(self, element):
        out = []
        current = element
        while True:
            parent = self.parent_of(current)
            if parent is None:
                return out
            out.append(parent)
            current = parent

    # -- ids -----------------------------------------------------------------

    def all_ids(self):
        return [e.id for e in self.elements()]

    def duplicate_ids(self):
        seen, dupes = set(), []
        for element_id in self.all_ids():
            if element_id in seen and element_id not in dupes:
                dupes.append(element_id)
            seen.add(element_id)
        return dupes

    def malformed_ids(self):
        return [i for i in self.all_ids()
                if not isinstance(i, str) or not ID_SHAPE.match(i)]

    def new_id(self):
        taken = set(self.all_ids())
        for _ in range(1000):
            candidate = secrets.token_hex(4)[:7]
            if candidate not in taken:
                return candidate
        raise DocumentError("could not allocate a free element id")  # pragma: no cover

    def element_model(self):
        for element in self.elements():
            if element.el_type in CONTAINER_TYPES:
                return "container"
        return "classic"

    # -- editing -------------------------------------------------------------

    def set_setting(self, element_id, key, value):
        self.by_id(element_id).settings[key] = value

    def unset_setting(self, element_id, key):
        settings = self.by_id(element_id).settings
        if key not in settings:
            raise DocumentError(
                "element %s has no setting %r, so there is nothing to unset. Run "
                "`inspect --element %s` to see what it does have."
                % (element_id, key, element_id)
            )
        del settings[key]

    def _container_for(self, element_id):
        element = self.by_id(element_id)
        if element.el_type == "widget":
            raise DocumentError(
                "%s is a widget (%s); widgets cannot contain other elements. Target a "
                "column instead." % (element_id, element.widget_type)
            )
        if element.raw.get("elements") is None:
            element.raw["elements"] = []
        return element

    def add_widget(self, parent_id, widget_type, settings=None, index=None):
        parent = self._container_for(parent_id)
        if parent.el_type == "section":
            raise DocumentError(
                "%s is a section; in the classic element model a widget goes inside a "
                "column. Add it to one of this section's columns."
                % parent_id
            )
        new_id = self.new_id()
        raw = {
            "id": new_id,
            "elType": "widget",
            "widgetType": widget_type,
            "isInner": False,
            "settings": dict(settings or {}),
            "elements": [],
        }
        children = parent.raw["elements"]
        if index is None:
            children.append(raw)
        else:
            children.insert(max(0, min(index, len(children))), raw)
        return new_id

    def add_column(self, section_id, size=100, index=None):
        section = self._container_for(section_id)
        if section.el_type != "section":
            raise DocumentError("%s is a %s; columns belong to sections."
                                % (section_id, section.el_type))
        new_id = self.new_id()
        raw = {
            "id": new_id,
            "elType": "column",
            "isInner": bool(section.raw.get("isInner")),
            "settings": {"_column_size": size, "_inline_size": None},
            "elements": [],
        }
        children = section.raw["elements"]
        if index is None:
            children.append(raw)
        else:
            children.insert(max(0, min(index, len(children))), raw)
        return new_id

    def remove(self, element_id):
        target = self.by_id(element_id).raw
        parent = self.parent_of(Element(target))
        siblings = self._content if parent is None else parent.raw["elements"]
        for index, raw in enumerate(siblings):
            if raw is target:
                return siblings.pop(index)
        raise DocumentError("could not detach %s" % element_id)  # pragma: no cover

    def insert_raw(self, parent_id, raw, index=None):
        """Re-attach a previously removed subtree, keeping its ids."""
        if parent_id is None:
            siblings = self._content
        else:
            siblings = self._container_for(parent_id).raw["elements"]
        if index is None:
            siblings.append(raw)
        else:
            siblings.insert(max(0, min(index, len(siblings))), raw)

    def move(self, element_id, before=None, after=None, into=None, index=None):
        if sum(1 for x in (before, after, into) if x) != 1:
            raise DocumentError("move needs exactly one of --before, --after or --into")

        target = self.by_id(element_id)
        anchor_id = before or after or into
        anchor = self.by_id(anchor_id)

        if anchor.id == target.id:
            raise DocumentError("cannot move %s relative to itself" % element_id)
        if any(a.id == target.id for a in self.ancestors_of(anchor)):
            raise DocumentError(
                "cannot move %s into its own descendant %s" % (element_id, anchor_id)
            )

        raw = self.remove(element_id)

        if into:
            self.insert_raw(anchor_id, raw, index)
            return

        parent = self.parent_of(anchor)
        siblings = self._content if parent is None else parent.raw["elements"]
        position = next(i for i, s in enumerate(siblings) if s is anchor.raw)
        siblings.insert(position if before else position + 1, raw)
