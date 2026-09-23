"""Access to the generated control projection.

The projection is produced by ``tools/crecs-template-studio/build-references.js`` from
the delivery-1 catalog and ships inside the package. Nothing here queries WordPress,
and nothing here is hand-maintained: if a control is missing, the answer is to
regenerate the catalog, never to add the control by hand.
"""

import hashlib
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_ROOT = os.path.dirname(os.path.dirname(_HERE))  # skill root
DEFAULT_PROJECTION = os.path.join(
    _PACKAGE_ROOT, "references", "catalog", "crecs-controls.min.json"
)
DEFAULT_FIELDS = os.path.join(
    _PACKAGE_ROOT, "references", "catalog", "crecs-property-fields.json"
)
DEFAULT_MANIFEST = os.path.join(
    _PACKAGE_ROOT, "references", "catalog", "MANIFEST.sha256"
)
REFERENCES_DIR = os.path.join(_PACKAGE_ROOT, "references")


class CatalogError(Exception):
    pass


class Control:
    """One control as the projection describes it."""

    __slots__ = ("name", "widget", "data")

    def __init__(self, name, widget, data):
        self.name = name
        self.widget = widget
        self.data = data

    def __getattr__(self, item):
        if item in self.__slots__:  # pragma: no cover
            raise AttributeError(item)
        return self.data.get(item)

    @property
    def is_responsive(self):
        return bool(self.data.get("is_responsive"))

    @property
    def options(self):
        return self.data.get("options")

    @property
    def open_vocabulary(self):
        return bool(self.data.get("open_vocabulary"))

    @property
    def accepts_dynamic(self):
        return bool(self.data.get("dynamic"))

    def source_ref(self):
        src = self.data.get("source")
        if not src:
            return None
        return "%s:%s" % (src.get("file"), src.get("line"))


class Catalog:
    def __init__(self, projection, fields):
        self.raw = projection
        self.fields = fields
        self._widgets = projection.get("widgets", {})
        self._core = projection.get("core_widgets", {})
        self._elements = projection.get("element_types", {})
        self._common = projection.get("common_controls", {})

    # -- loading -------------------------------------------------------------

    @classmethod
    def load(cls, projection_path, fields_path):
        for path in (projection_path, fields_path):
            if not os.path.isfile(path):
                raise CatalogError(
                    "catalog file missing: %s. The package is incomplete; re-extract "
                    "it or regenerate with tools/crecs-template-studio/"
                    "build-references.js." % path
                )
        with open(projection_path, encoding="utf-8") as fh:
            projection = json.load(fh)
        with open(fields_path, encoding="utf-8") as fh:
            fields = json.load(fh)
        return cls(projection, fields)

    @classmethod
    def load_default(cls):
        return cls.load(DEFAULT_PROJECTION, DEFAULT_FIELDS)

    # -- provenance ----------------------------------------------------------

    @property
    def provenance(self):
        return self.raw.get("provenance", {})

    def fingerprint(self):
        """Identifies the catalog this package carries, for the workspace state."""
        prov = self.provenance
        return {
            "catalog_sha256": prov.get("catalog_sha256"),
            "plugin_revision": prov.get("plugin_revision"),
            "crecs_plugin": prov.get("crecs_plugin"),
            "elementor": prov.get("elementor"),
            "projection_sha256": hashlib.sha256(
                json.dumps(self.raw, sort_keys=True).encode("utf-8")
            ).hexdigest(),
        }

    # -- responsive ----------------------------------------------------------

    @property
    def devices(self):
        return list(self.raw.get("responsive", {}).get("devices", []))

    @property
    def responsive_rule(self):
        return self.raw.get("responsive", {}).get("rule", "")

    @property
    def supported_export_versions(self):
        return list(self.raw.get("supported_export_versions", []))

    @property
    def placeholder_values(self):
        return list(self.raw.get("elementor_placeholder_values", []))

    # -- widgets -------------------------------------------------------------

    def widget_names(self, relevance=None):
        names = sorted(self._widgets)
        if relevance is None:
            return names
        wanted = {relevance} if isinstance(relevance, str) else set(relevance)
        return [n for n in names if self._widgets[n].get("relevance") in wanted]

    def relevant_widget_names(self):
        return [n for n in sorted(self._widgets)
                if self._widgets[n].get("relevance") != "excluded"]

    def widget(self, name):
        return self._widgets.get(name)

    def knows_widget(self, name):
        return name in self._widgets or name in self._core

    def is_crecs_widget(self, name):
        return name in self._widgets

    def is_core_widget(self, name):
        return name in self._core

    def knows_element_type(self, el_type):
        return el_type in self._elements

    def widget_title(self, name):
        entry = self._widgets.get(name) or self._core.get(name) or {}
        return entry.get("title") or name

    def relevance(self, name):
        entry = self._widgets.get(name)
        return entry.get("relevance") if entry else None

    def max_instances(self, name):
        entry = self._widgets.get(name)
        return entry.get("max_instances") if entry else None

    def cardinality_reason(self, name):
        entry = self._widgets.get(name)
        return (entry or {}).get("cardinality_reason")

    def must_be_first(self, name):
        entry = self._widgets.get(name)
        return bool(entry and entry.get("must_be_first"))

    def legacy_aliases(self, name):
        entry = self._widgets.get(name)
        return dict((entry or {}).get("legacy_aliases") or {})

    def sections(self, name):
        entry = self._widgets.get(name) or self._core.get(name) or {}
        return entry.get("sections") or []

    # -- controls ------------------------------------------------------------

    def _controls_for(self, kind, name):
        if kind == "widget":
            entry = self._widgets.get(name) or self._core.get(name)
        else:
            entry = self._elements.get(name)
        return (entry or {}).get("controls") or {}

    def control(self, owner, control_name, el_type="widget"):
        """Look up a control on a widget/element, falling back to the common set."""
        own = self._controls_for(el_type, owner)
        if control_name in own:
            return Control(control_name, owner, own[control_name])
        if control_name in self._common:
            return Control(control_name, owner, self._common[control_name])
        return None

    def controls(self, owner, el_type="widget"):
        own = self._controls_for(el_type, owner)
        return {k: Control(k, owner, v) for k, v in own.items()}

    def common_control(self, control_name):
        data = self._common.get(control_name)
        return Control(control_name, None, data) if data else None

    def is_common(self, control_name):
        return control_name in self._common

    def common_owner(self, control_name):
        return (self._common.get(control_name) or {}).get("owner")

    def split_device_suffix(self, control_name):
        """('card_margin', 'mobile') for card_margin_mobile, else (name, None)."""
        for device in self.devices:
            suffix = "_" + device
            if control_name.endswith(suffix):
                return control_name[: -len(suffix)], device
        return control_name, None

    def known_device_suffixes(self):
        return list(self.devices)

    def all_device_like_suffixes(self):
        """Suffixes Elementor could have used on some other site's breakpoints.

        Used to tell "you meant a device variant but that breakpoint is off here"
        apart from "this key is simply unknown".
        """
        return ["widescreen", "laptop", "tablet_extra", "mobile_extra", "desktop"]

    # -- dynamic tags --------------------------------------------------------

    def dynamic_tag(self, name):
        return (self.raw.get("dynamic_tags") or {}).get(name)

    def dynamic_tag_names(self):
        return sorted(self.raw.get("dynamic_tags") or {})

    def property_params(self):
        return [f["param_name"] for f in self.fields.get("params", [])]

    def bindable_property_params(self):
        return [f["param_name"] for f in self.fields.get("params", [])
                if f.get("bindable_scalar")]

    def param_detail(self, param_name):
        for entry in self.fields.get("params", []):
            if entry["param_name"] == param_name:
                return entry
        return None

    def suggest_param(self, wanted):
        """Case-insensitive match first — the documented keys got the casing wrong
        (``size-available_sf`` vs ``size-available_SF``), so that is the most likely
        mistake."""
        params = self.property_params()
        lowered = {p.lower(): p for p in params}
        if wanted.lower() in lowered:
            return lowered[wanted.lower()]
        return _closest(wanted, params)

    def dangerous_tags(self):
        return self.raw.get("dangerous_tags") or {}

    # -- naming help ---------------------------------------------------------

    def non_existent_names(self):
        return self.raw.get("non_existent_names") or {}

    def naming_hazards(self, widget=None):
        hazards = self.raw.get("naming_hazards") or {}
        return hazards.get(widget) if widget else hazards

    def suggest_widget(self, wanted):
        known = self.non_existent_names().get(wanted)
        if known and known.get("real_name"):
            return known["real_name"], known.get("note")
        if known:
            return None, known.get("note")
        candidates = list(self._widgets) + list(self._core)
        return _closest(wanted, candidates), None

    def suggest_control(self, widget, wanted):
        """Suggest the current name for a control the widget does not have."""
        aliases = self.legacy_aliases(widget)
        if wanted in aliases:
            return aliases[wanted], "renamed in a later plugin version"
        own = self._controls_for("widget", widget)
        base, device = self.split_device_suffix(wanted)
        if device and base in own:
            return base, "that control is not responsive, so there is no %s variant" % device
        if base in aliases:
            return aliases[base], "renamed in a later plugin version"
        return _closest(wanted, list(own)), None


def _closest(wanted, candidates):
    """Cheap edit-distance pick, stdlib only."""
    import difflib
    matches = difflib.get_close_matches(wanted, candidates, n=1, cutoff=0.6)
    return matches[0] if matches else None
