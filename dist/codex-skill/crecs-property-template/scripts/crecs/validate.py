"""The validator.

ERROR blocks a "ready" export. WARNING and INFO never do.

The line that matters most: a setting **introduced now** with no confirmed contract
is an ERROR, while a setting that was **already in the document at import** is
preserved and reported as a WARNING. Deleting somebody else's add-on data because
this package has not heard of it would be worse than shipping it forward.

A visual preference is reported as INFO and never dressed up as a technical limit.
"""

import re

from . import bindings as bindings_mod
from .document import DocumentError

ERROR = "ERROR"
WARNING = "WARNING"
INFO = "INFO"

_HEX_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGBA = re.compile(r"^rgba?\(")
_GLOBAL_REF = re.compile(r"^globals/")

# Deliberately narrow: these match shapes that are unmistakably credentials, so a
# colour or a slug can never trip them.
_SECRET_PATTERNS = [
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{30,}")),
    ("bearer-token", re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{5,}")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("slack-token", re.compile(r"\bxox[abprs]-[0-9A-Za-z\-]{10,}")),
    ("github-token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{20,}")),
]

_PLACEHOLDER_LINKS = ("#", "", "http://#", "https://#")


class Finding:
    __slots__ = ("code", "severity", "message", "element_id", "path", "control", "hint")

    def __init__(self, code, severity, message, element_id=None, path=None,
                 control=None, hint=None):
        self.code = code
        self.severity = severity
        self.message = message
        self.element_id = element_id
        self.path = path
        self.control = control
        self.hint = hint

    def to_dict(self):
        out = {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        for key in ("element_id", "path", "control", "hint"):
            value = getattr(self, key)
            if value:
                out[key] = value
        return out

    def __repr__(self):  # pragma: no cover
        return "<%s %s %s>" % (self.severity, self.code, self.message[:60])


class Result:
    def __init__(self, findings, summary):
        self.findings = findings
        self.summary = summary
        self.counts = {ERROR: 0, WARNING: 0, INFO: 0}
        for finding in findings:
            self.counts[finding.severity] = self.counts.get(finding.severity, 0) + 1

    @property
    def is_exportable(self):
        return self.counts.get(ERROR, 0) == 0

    def by_severity(self, severity):
        return [f for f in self.findings if f.severity == severity]

    def to_dict(self):
        return {
            "counts": self.counts,
            "exportable": self.is_exportable,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
        }


class _Run:
    def __init__(self, document, catalog, profile, baseline_keys):
        self.doc = document
        self.cat = catalog
        self.profile = profile
        self.baseline = set(baseline_keys or ())
        self.findings = []
        self.bound_params = set()
        self.declared_unknown_widgets = set()
        self.not_catalogued_reported = set()

    # -- emit ----------------------------------------------------------------

    def add(self, code, severity, message, element=None, control=None, hint=None):
        self.findings.append(Finding(
            code, severity, message,
            element_id=element.id if element is not None else None,
            path=self.doc.path_of(element) if element is not None else None,
            control=control,
            hint=hint,
        ))

    def preexisting(self, element, key):
        return "%s::%s" % (element.id, key) in self.baseline

    def _is_bound(self, element, control_name):
        """True when a dynamic tag is attached to this control, in which case
        Elementor ignores the static value stored beside it."""
        dynamic = element.settings.get("__dynamic__")
        return isinstance(dynamic, dict) and control_name in dynamic

    # -- envelope ------------------------------------------------------------

    def check_envelope_strings(self):
        """The envelope's own fields (title, page_settings) travel with the export, so
        they get the same secret and frozen-content scan as element settings."""
        if self.doc.envelope is None:
            return
        for key in ("title", "type", "page_settings"):
            if key not in self.doc.envelope:
                continue
            value = self.doc.envelope[key]
            for text in _strings_in(value):
                for label, pattern in _SECRET_PATTERNS:
                    if pattern.search(text):
                        self.add("E-SECRET", ERROR,
                                 "The envelope field %r contains something shaped like "
                                 "a %s. Credentials must never travel inside a "
                                 "template." % (key, label))
                        return
            for literal in self.profile.forbidden_literals:
                for text in _strings_in(value):
                    if literal and literal in text:
                        self.add("E-FROZEN-CONTENT", ERROR,
                                 "The envelope field %r contains %r, which the target "
                                 "profile lists as content that must not be frozen "
                                 "into the template." % (key, literal))
                        return

    def check_envelope(self):
        supported = self.cat.supported_export_versions
        version = self.doc.export_version
        if self.doc.envelope is None:
            self.add("W-ENVELOPE-BARE", WARNING,
                     "This document is a bare element array with no envelope. Elementor "
                     "can import it, but the export will have no version, title or "
                     "type. Supported envelope versions: %s." % ", ".join(supported))
            return
        if version is None:
            self.add("W-ENVELOPE-VERSION-MISSING", WARNING,
                     "The envelope has no 'version'. Elementor stamps the export "
                     "schema version there; %s is what this catalog was built against."
                     % ", ".join(supported))
        elif version not in supported:
            self.add("E-ENVELOPE-VERSION", ERROR,
                     "Export schema version %r is not supported by this package "
                     "(supported: %s). This is the Elementor *export format* version, "
                     "not the Elementor plugin version."
                     % (version, ", ".join(supported)))
        if not self.doc.doc_type:
            self.add("W-ENVELOPE-TYPE", WARNING,
                     "The envelope has no 'type'. A property page template should be "
                     "type \"page\".")
        elif self.doc.doc_type != "page":
            self.add("W-ENVELOPE-TYPE", WARNING,
                     "Envelope type is %r; the shared property template is imported as "
                     "type \"page\"." % self.doc.doc_type)

    def check_element_model(self):
        if self.doc.element_model() != "classic":
            containers = [e for e in self.doc.elements() if e.el_type == "container"]
            self.add("E-ELEMENT-MODEL", ERROR,
                     "This document uses %d flexbox container element(s). The audited "
                     "site runs the classic section/column model (Elementor "
                     "'container' experiment = default, e_atomic_elements = false), and "
                     "containers use a completely different settings vocabulary. "
                     "Converting the template is out of scope." % len(containers),
                     element=containers[0])

    # -- ids and nesting -----------------------------------------------------

    def check_ids(self):
        for dupe in self.doc.duplicate_ids():
            self.add("E-ID-DUPLICATE", ERROR,
                     "Element id %r appears more than once. Elementor addresses "
                     "elements by id, so duplicates make edits land on the wrong one."
                     % dupe)
        for bad in self.doc.malformed_ids():
            self.add("E-ID-MALFORMED", ERROR,
                     "Element id %r is not 7-8 lowercase hex characters, which is what "
                     "Elementor generates." % bad)

    def check_nesting(self):
        for element in self.doc.elements():
            parent = self.doc.parent_of(element)
            el_type = element.el_type
            children = element.raw.get("elements") or []

            if el_type == "widget" and children:
                self.add("E-NESTING", ERROR,
                         "Widget %s (%s) has %d child element(s). Widgets are leaves."
                         % (element.id, element.widget_type, len(children)),
                         element=element)
            if el_type == "column":
                if parent is None or parent.el_type not in ("section", "container"):
                    self.add("E-NESTING", ERROR,
                             "Column %s is not inside a section." % element.id,
                             element=element)
            if el_type == "widget":
                if parent is None or parent.el_type not in ("column", "container"):
                    self.add("E-NESTING", ERROR,
                             "Widget %s (%s) is not inside a column. In the classic "
                             "element model widgets live in columns."
                             % (element.id, element.widget_type), element=element)
            if el_type == "section" and parent is not None:
                if parent.el_type != "column":
                    self.add("E-NESTING", ERROR,
                             "Section %s is nested inside a %s; an inner section "
                             "belongs to a column." % (element.id, parent.el_type),
                             element=element)
                elif not element.raw.get("isInner"):
                    self.add("W-NESTING-INNER", WARNING,
                             "Section %s sits inside a column but is not marked "
                             "isInner. Elementor sets isInner on nested sections."
                             % element.id, element=element)

    # -- loader, order, cardinality -----------------------------------------

    def check_loader_and_cardinality(self):
        widgets = self.doc.widgets()
        loaders = [w for w in widgets if w.widget_type == "crecs_property_data"]
        property_widgets = [w for w in widgets
                            if self.cat.is_crecs_widget(w.widget_type or "")
                            and self.cat.relevance(w.widget_type) in
                            ("core", "non_visual", "required")]

        if not loaders:
            if property_widgets:
                self.add("E-LOADER-MISSING", ERROR,
                         "No crecs_property_data widget, but %d property widget(s) are "
                         "present. The loader is what resolves the property and writes "
                         "it into the PHP session ($_SESSION['property']); every other "
                         "property widget reads that key in its own render(). Without "
                         "it they render whatever the session last held, or nothing. "
                         "Alternative: if you truly want a page with no property data, "
                         "remove the property widgets too."
                         % len(property_widgets))
            else:
                self.add("W-LOADER-MISSING", WARNING,
                         "No crecs_property_data widget. This document carries no "
                         "property data at all.")
        elif widgets and widgets[0].widget_type != "crecs_property_data":
            self.add("E-LOADER-ORDER", ERROR,
                     "crecs_property_data is not the first widget in document order "
                     "(%s is). Elementor renders in order and the loader writes the "
                     "session value the others read, so anything before it renders "
                     "with a stale or empty property."
                     % widgets[0].widget_type, element=widgets[0])

        counts = {}
        for widget in widgets:
            counts.setdefault(widget.widget_type, []).append(widget)
        for widget_type, instances in sorted(counts.items()):
            limit = self.cat.max_instances(widget_type)
            if limit is None or len(instances) <= limit:
                continue
            reason = self.cat.cardinality_reason(widget_type) or "unknown reason"
            self.add("E-CARDINALITY", ERROR,
                     "%d instances of %s, but at most %d can work on one page. %s"
                     % (len(instances), widget_type, limit, reason),
                     element=instances[1],
                     hint="Keep one instance and move or delete the others.")

    def check_coverage(self):
        present = {w.widget_type for w in self.doc.widgets()}
        expected = [n for n in self.cat.relevant_widget_names()
                    if self.cat.relevance(n) in ("required", "core", "non_visual")]
        missing = [n for n in expected if n not in present]
        if missing:
            self.add("W-COVERAGE", WARNING,
                     "%d relevant widget(s) are absent from this document: %s. That is "
                     "fine if it was a deliberate choice; the catalog still supports "
                     "them and they can be added back."
                     % (len(missing), ", ".join(missing)))
        if "crecs_property_meta_tags" in missing:
            self.add("W-META-TAGS-MISSING", WARNING,
                     "crecs_property_meta_tags is absent. On the Elementor template "
                     "path that widget is what emits the per-property <title>, meta "
                     "description and Open Graph tags from inside the template.")

    # -- settings ------------------------------------------------------------

    def check_settings(self):
        for element in self.doc.elements():
            try:
                settings = element.settings
            except DocumentError as exc:
                self.add("E-ENVELOPE-SHAPE", ERROR, str(exc), element=element)
                continue

            owner, el_kind = self._owner_of(element)
            if owner is None:
                continue

            for key in sorted(settings):
                if key == "__dynamic__":
                    continue
                self._check_one_setting(element, owner, el_kind, key, settings[key])

    def _owner_of(self, element):
        if element.el_type == "widget":
            widget_type = element.widget_type
            if not widget_type:
                self.add("E-ENVELOPE-SHAPE", ERROR,
                         "Element %s has elType 'widget' but no widgetType."
                         % element.id, element=element)
                return None, None
            if self.cat.knows_widget(widget_type):
                return widget_type, "widget"
            if widget_type not in self.declared_unknown_widgets:
                self.declared_unknown_widgets.add(widget_type)
                real, note = self.cat.suggest_widget(widget_type)
                message = ("Widget type %r is not in this catalog, so its settings are "
                           "preserved as-is and not validated." % widget_type)
                if real:
                    message += " Did you mean %r?" % real
                if note:
                    message += " " + note
                self.add("W-WIDGET-UNKNOWN", WARNING, message, element=element)
            return None, None
        if self.cat.knows_element_type(element.el_type):
            return element.el_type, "element"
        return None, None

    def _check_one_setting(self, element, owner, el_kind, key, value):
        # Secrets first: they matter whatever the key is.
        self._check_secret(element, key, value)
        self._check_frozen_literal(element, key, value)
        self._check_asset(element, key, value)

        control = self.cat.control(owner, key, el_type=el_kind)
        base, device = self.cat.split_device_suffix(key)

        if control is None and device:
            base_control = self.cat.control(owner, base, el_type=el_kind)
            if base_control is not None:
                if base_control.is_responsive:
                    control = base_control
                else:
                    self.add("E-RESPONSIVE-UNSUPPORTED", ERROR,
                             "%s sets %r, but %r is not a responsive control on %s "
                             "(is_responsive is false), so Elementor never reads the "
                             "device variant." % (element.id, key, base, owner),
                             element=element, control=key,
                             hint="Set %r for all devices instead." % base)
                    return

        if control is None:
            for suffix in self.cat.all_device_like_suffixes():
                if key.endswith("_" + suffix):
                    trunk = key[: -(len(suffix) + 1)]
                    if self.cat.control(owner, trunk, el_type=el_kind):
                        self.add("E-RESPONSIVE-DEVICE", ERROR,
                                 "%s sets %r, but %r is not an active breakpoint on "
                                 "this site (active: %s), so the value is dead."
                                 % (element.id, key, suffix,
                                    ", ".join(self.cat.devices)),
                                 element=element, control=key)
                        return

        if control is None:
            self._report_unknown_key(element, owner, key)
            return

        self._check_value(element, owner, key, control, value)
        self._check_condition(element, owner, key, control)

    def _report_unknown_key(self, element, owner, key):
        suggestion, why = self.cat.suggest_control(owner, key)

        if key.startswith("_"):
            # Elementor owns the underscore namespace and writes several keys there
            # that are not registered controls — `_column_size` on every column is the
            # obvious one. Blocking them would block every real Elementor export, and
            # this package has no standing to call them invented.
            self.add("I-ELEMENTOR-INTERNAL-KEY", INFO,
                     "%s carries %r, which is in Elementor's own underscore namespace "
                     "but is not a registered control on %s. Elementor writes a few of "
                     "these itself; it is preserved untouched."
                     % (element.id, key, owner),
                     element=element, control=key)
            return

        if self.preexisting(element, key):
            message = ("%s carries %r, which %s does not register. It was already in "
                       "the document at import, so it is kept untouched and Elementor "
                       "will ignore it." % (element.id, key, owner))
            code = "W-KEY-PREEXISTING-UNKNOWN"
            if suggestion:
                self.add("W-LEGACY-ALIAS", WARNING,
                         "%s: %r is a key from an older export; the control that "
                         "replaced it is %r%s."
                         % (element.id, key, suggestion,
                            " (" + why + ")" if why else ""),
                         element=element, control=key,
                         hint="Copy the value to %r if the styling is still wanted."
                              % suggestion)
            self.add(code, WARNING, message, element=element, control=key)
            return

        message = ("%s sets %r, which is not a control registered by %s. Nothing "
                   "confirms what Elementor would do with it, so it is blocked."
                   % (element.id, key, owner))
        if suggestion:
            message += " Closest registered control: %r%s." % (
                suggestion, " (" + why + ")" if why else ""
            )
        self.add("E-CONTROL-UNKNOWN", ERROR, message, element=element, control=key,
                 hint="Run `catalog --widget %s --controls` for the full list." % owner)

    # -- value checks --------------------------------------------------------

    def _check_value(self, element, owner, key, control, value):
        if value is None:
            # Elementor writes null for an unset control (for example a column's
            # _inline_size). Absent and null are the same thing to it.
            return

        ctype = control.type
        checker = getattr(self, "_v_" + (ctype or "").replace("-", "_"), None)
        if checker:
            checker(element, owner, key, control, value)

        options = control.options
        if options and isinstance(value, (int, float)) and not isinstance(value, bool) \
                and all(isinstance(o, str) for o in options):
            matches = str(value) in options
            if self.preexisting(element, key):
                # Elementor's own exports contain numeric font weights. The CSS
                # generator still emits them; it is the editor's select that shows the
                # control as unset. Report, do not block.
                self.add("W-OPTION-NUMERIC", WARNING,
                         "%s stores %s as the number %r while this control's options "
                         "are strings. Elementor still writes the CSS, but the editor "
                         "will show the control as unset%s."
                         % (element.id, key, value,
                            "" if matches else " and the value is not even in the list"),
                         element=element, control=key,
                         hint="Store it as the string %r." % str(value))
            else:
                self.add("E-CONTROL-TYPE", ERROR,
                         "%s sets %s to the number %r, but this control's options are "
                         "strings (%s). Elementor compares option values as strings, so "
                         "the number will not match."
                         % (element.id, key, value,
                            ", ".join(repr(o) for o in options[:8])),
                         element=element, control=key,
                         hint="Store it as the string %r." % str(value))
            return

        if options is not None and isinstance(value, str) and value != "":
            if value not in options:
                if self.preexisting(element, key):
                    # Elementor renames option values between versions and keeps
                    # honouring the old ones (align: left -> start, button_size:
                    # sm -> auto). A value that was already in the document is
                    # reported, not blocked.
                    self.add("W-OPTION-LEGACY-VALUE", WARNING,
                             "%s sets %s=%r, which is not in the option list this "
                             "Elementor version registers (%s). It was already in the "
                             "document, so it is kept: Elementor generally still "
                             "honours renamed option values, but the editor will show "
                             "the control as unset."
                             % (element.id, key, value,
                                ", ".join(repr(o) for o in options)),
                             element=element, control=key,
                             hint="Re-pick the value in the editor, or set it to one of "
                                  "the current options.")
                elif control.open_vocabulary:
                    self.add("I-OPEN-VOCABULARY", INFO,
                             "%s sets %s=%r, which is not in the captured option list. "
                             "That list is site-derived (%s), so an unlisted value is "
                             "normal; it has to exist on the target site."
                             % (element.id, key, value,
                                control.data.get("open_vocabulary_reason")),
                             element=element, control=key)
                else:
                    self.add("E-CONTROL-OPTION", ERROR,
                             "%s sets %s=%r, but the registered options are: %s."
                             % (element.id, key, value, ", ".join(repr(o) for o in options)),
                             element=element, control=key)
        elif options is None and control.open_vocabulary and isinstance(value, str) \
                and value != "":
            self.add("I-OPEN-VOCABULARY", INFO,
                     "%s sets %s=%r. This control's options are site-derived (%s), so "
                     "the value cannot be checked offline; confirm it exists on the "
                     "target site."
                     % (element.id, key, value,
                        control.data.get("open_vocabulary_reason")),
                     element=element, control=key)

    def _type_error(self, element, key, control, value, expected):
        self.add("E-CONTROL-TYPE", ERROR,
                 "%s sets %s to %s, but a %r control stores %s."
                 % (element.id, key, _describe(value), control.type, expected),
                 element=element, control=key)

    def _v_dimensions(self, element, owner, key, control, value):
        if not isinstance(value, dict):
            return self._type_error(element, key, control, value,
                                    "an object { unit, top, right, bottom, left, "
                                    "isLinked }")
        self._check_unit(element, key, control, value)

    def _v_slider(self, element, owner, key, control, value):
        if not isinstance(value, dict):
            return self._type_error(element, key, control, value,
                                    "an object { unit, size, sizes }")
        self._check_unit(element, key, control, value)

    def _check_unit(self, element, key, control, value):
        units = control.data.get("size_units")
        unit = value.get("unit")
        if units and unit is not None and unit not in units:
            self.add("E-CONTROL-UNIT", ERROR,
                     "%s sets %s with unit %r, but the control accepts %s."
                     % (element.id, key, unit, ", ".join(units)),
                     element=element, control=key)

    def _v_color(self, element, owner, key, control, value):
        if not isinstance(value, str):
            return self._type_error(element, key, control, value,
                                    "a string (hex or rgba)")
        if value == "" or _GLOBAL_REF.match(value):
            return
        if _HEX_COLOR.match(value) or _RGBA.match(value):
            self.add("I-LITERAL-COLOR", INFO,
                     "%s sets %s to the literal colour %s. That is a preference, not a "
                     "problem; binding it to an Elementor global colour would make a "
                     "palette change one edit instead of many."
                     % (element.id, key, value),
                     element=element, control=key)
            return
        self.add("W-COLOR-SHAPE", WARNING,
                 "%s sets %s=%r, which is neither a hex colour, an rgb()/rgba() value "
                 "nor a globals/ reference." % (element.id, key, value),
                 element=element, control=key)

    def _v_switcher(self, element, owner, key, control, value):
        expected = control.data.get("return_value", "yes")
        if isinstance(value, bool) or not isinstance(value, str):
            return self._type_error(
                element, key, control, value,
                'the string %r when on and "" when off (never a boolean)' % expected
            )
        if value not in ("", expected):
            self.add("E-CONTROL-TYPE", ERROR,
                     "%s sets %s=%r; a switcher stores %r or \"\"."
                     % (element.id, key, value, expected),
                     element=element, control=key)

    def _v_number(self, element, owner, key, control, value):
        if isinstance(value, bool):
            return self._type_error(element, key, control, value, "a number")
        if isinstance(value, (int, float)):
            return
        if isinstance(value, str) and (value == "" or _is_numeric(value)):
            return
        self._type_error(element, key, control, value, "a number or numeric string")

    def _v_select(self, element, owner, key, control, value):
        if value is not None and not isinstance(value, (str, int, float)):
            self._type_error(element, key, control, value, "a string")

    def _v_select2(self, element, owner, key, control, value):
        if control.data.get("multiple"):
            if value not in ("", None) and not isinstance(value, list):
                self._type_error(element, key, control, value, "an array of strings")
        elif value is not None and not isinstance(value, (str, int, float)):
            self._type_error(element, key, control, value, "a string")

    def _v_media(self, element, owner, key, control, value):
        if value in ("", None):
            return
        if not isinstance(value, dict):
            self._type_error(element, key, control, value, "an object { id, url }")

    def _v_url(self, element, owner, key, control, value):
        if value in ("", None):
            return
        if not isinstance(value, dict):
            return self._type_error(element, key, control, value,
                                    "an object { url, is_external, nofollow }")
        url = value.get("url")
        if self._is_bound(element, key):
            if isinstance(url, str) and url.strip() in _PLACEHOLDER_LINKS:
                self.add("I-SHADOWED-BY-BINDING", INFO,
                         "%s keeps a static %s of %r, but that control also carries a "
                         "dynamic binding, which wins. The leftover value is harmless "
                         "and is preserved." % (element.id, key, url),
                         element=element, control=key)
            return
        if isinstance(url, str) and url.strip() in _PLACEHOLDER_LINKS:
            self.add("E-DEP-PLACEHOLDER-LINK", ERROR,
                     "%s sets %s to the placeholder link %r. A '#' link looks "
                     "functional and is not: either bind the control to a real target "
                     "(a crecs-property url field, or an Elementor Pro popup declared "
                     "in the target profile) or remove the element."
                     % (element.id, key, url),
                     element=element, control=key)

    def _v_repeater(self, element, owner, key, control, value):
        if value is None:
            return
        if not isinstance(value, list):
            return self._type_error(element, key, control, value,
                                    "an array of row objects")
        for index, row in enumerate(value):
            if not isinstance(row, dict):
                self.add("E-REPEATER-SHAPE", ERROR,
                         "%s: %s[%d] is %s; a repeater row is an object."
                         % (element.id, key, index, _describe(row)),
                         element=element, control=key)
                continue
            if "_id" not in row:
                self.add("E-REPEATER-SHAPE", ERROR,
                         "%s: %s[%d] has no '_id'. Elementor gives every repeater row "
                         "an _id and uses it to address the row."
                         % (element.id, key, index),
                         element=element, control=key)

    def _v_font(self, element, owner, key, control, value):
        if not isinstance(value, str):
            return self._type_error(element, key, control, value,
                                    "a string (font family name)")
        if value:
            self.add("I-FONT-FAMILY", INFO,
                     "%s sets %s to the literal font family %r. The target site has to "
                     "be able to load it." % (element.id, key, value),
                     element=element, control=key)

    def _v_popover_toggle(self, element, owner, key, control, value):
        if not isinstance(value, str):
            self._type_error(element, key, control, value,
                             'a string ("" or "custom"/"yes")')

    # -- conditions ----------------------------------------------------------

    def _check_condition(self, element, owner, key, control):
        condition = control.data.get("condition")
        if not condition:
            return
        settings = element.settings
        for dep_key, expected in condition.items():
            negate = dep_key.endswith("!")
            name = dep_key[:-1] if negate else dep_key
            dep_control = self.cat.control(owner, name)
            actual = settings.get(name)
            if actual is None and dep_control is not None:
                actual = dep_control.data.get("default")
            wanted = expected if isinstance(expected, list) else [expected]
            matches = actual in wanted
            if negate:
                matches = not matches
            if not matches:
                self.add("I-CONDITION-UNMET", INFO,
                         "%s sets %s, but that control only appears in the editor when "
                         "%s. The value is stored and simply not applied."
                         % (element.id, key, _describe_condition(dep_key, expected)),
                         element=element, control=key)

    # -- bindings ------------------------------------------------------------

    def check_bindings(self):
        for element in self.doc.elements():
            try:
                settings = element.settings
            except DocumentError:
                continue
            for binding in bindings_mod.read_element_bindings(settings):
                self._check_binding(element, binding)

    def _check_binding(self, element, binding):
        tag = binding.tag
        if binding.error:
            self.add("E-BINDING-CORRUPT", ERROR,
                     "%s has an unreadable dynamic binding on %r: %s"
                     % (element.id, binding.control, binding.error),
                     element=element, control=binding.control)
            return

        owner = element.widget_type if element.el_type == "widget" else element.el_type
        if tag.name in self.cat.dangerous_tags():
            info = self.cat.dangerous_tags()[tag.name]
            self.add("E-BINDING-FORBIDDEN-TAG", ERROR,
                     "%s binds %r through the %s tag. %s"
                     % (element.id, binding.control, tag.name, info.get("reason")),
                     element=element, control=binding.control)
            return

        if tag.name == "crecs-property":
            param = tag.settings.get("param_name")
            if not param:
                self.add("E-BINDING-PARAM", ERROR,
                         "%s binds %r to crecs-property with no param_name, so it "
                         "renders nothing." % (element.id, binding.control),
                         element=element, control=binding.control)
                return
            if param not in self.cat.property_params():
                suggestion = self.cat.suggest_param(param)
                message = ("%s binds %r to crecs-property param_name=%r, which "
                           "Crecs_Functions::crecs_parse_property_data() never "
                           "produces." % (element.id, binding.control, param))
                if suggestion:
                    message += (" The real key is %r — the array keys are compared "
                                "exactly, including case." % suggestion)
                self.add("E-BINDING-PARAM", ERROR, message,
                         element=element, control=binding.control)
                return
            self.bound_params.add(param)
            detail = self.cat.param_detail(param) or {}
            if not detail.get("bindable_scalar"):
                self.add("W-BINDING-NON-SCALAR", WARNING,
                         "%s binds %r to %r. That key exists but holds %s, and the tag "
                         "renders only strings and numbers, so it will print nothing. "
                         "%s" % (element.id, binding.control, param,
                                 "a collection" if detail.get("note") else "a non-scalar",
                                 detail.get("note") or ""),
                         element=element, control=binding.control)
            control = self.cat.control(owner, binding.control) if owner else None
            if control is not None and not control.accepts_dynamic:
                self.add("W-BINDING-TARGET", WARNING,
                         "%s binds %r, but that control is not registered as accepting "
                         "a dynamic tag." % (element.id, binding.control),
                         element=element, control=binding.control)
            return

        if tag.name == "popup":
            popup_id = tag.settings.get("popup")
            if not popup_id:
                self.add("E-BINDING-CORRUPT", ERROR,
                         "%s has an Elementor Pro popup binding on %r with no popup id."
                         % (element.id, binding.control),
                         element=element, control=binding.control)
            elif not self.profile.knows_popup(popup_id):
                self.add("E-DEP-UNRESOLVED", ERROR,
                         "%s binds %r to Elementor Pro popup id %s, which the target "
                         "profile does not declare. Popup ids are per-site; reusing the "
                         "source site's id points the button at nothing."
                         % (element.id, binding.control, popup_id),
                         element=element, control=binding.control,
                         # Deliberately NOT "declare %s in your profile". Declaring the
                         # source site's id is the trap, not the fix: the check would pass
                         # and the button would still open nothing. Retarget it instead.
                         hint="Pick the popup on the client's own site and retarget this "
                              "button: `popup --element %s --control %s --set <id>`. "
                              "`popup --list` shows what the template binds today. "
                              "Declaring %s in the profile would silence this check "
                              "without making the button work."
                              % (element.id, binding.control, popup_id))
            return

        self.add("I-BINDING-OTHER-TAG", INFO,
                 "%s binds %r through the %r dynamic tag, which is outside this "
                 "catalog; its payload is preserved untouched."
                 % (element.id, binding.control, tag.name),
                 element=element, control=binding.control)

    # -- dependencies, secrets, frozen content -------------------------------

    def check_profile_popups(self):
        """A popup key that is not a number cannot be a popup id.

        The shipped example profile carries placeholder keys on purpose, because it
        used to carry the reference site's own ids and anyone who copied it unedited
        got a clean validation and two dead buttons. Saying so here means the person
        is told what to do rather than left to notice the buttons later.
        """
        declared = (self.profile.data.get("popups") or {}) if not self.profile.is_empty() else {}
        for key in declared:
            text = str(key)
            if text.isdigit():
                continue
            self.add("W-PROFILE-POPUP-PLACEHOLDER", WARNING,
                     "The target profile declares a popup keyed %r, which is not a "
                     "post id. The key must be the Elementor Pro popup id on this "
                     "site; the value is only a label." % text,
                     hint="Replace the key with the real id, then point a button at it "
                          "with `popup --element <id> --control <control> --set <id>`.")

    def check_loader_slug(self):
        for widget in self.doc.widgets():
            if widget.widget_type != "crecs_property_data":
                continue
            slug = widget.settings.get("slug")
            if slug in (None, ""):
                self.add("E-DEP-UNRESOLVED", ERROR,
                         "The loader %s has an empty slug. That control is the "
                         "design-time fallback: on a /property/{slug} URL the widget "
                         "reads the slug from the URL, but in the Elementor editor and "
                         "on any other URL it falls back to this value. Empty means the "
                         "editor preview resolves no property."
                         % widget.id, element=widget, control="slug",
                         hint='Set "preview_slug" in the target profile, or '
                              '`set --element %s --key slug --value <slug>`.' % widget.id)
                continue
            if slug in self.profile.example_slugs:
                self.add("E-FROZEN-SLUG", ERROR,
                         "The loader %s still points at the example property %r. "
                         "Shipping it freezes another client's property into the "
                         "template." % (widget.id, slug),
                         element=widget, control="slug",
                         hint="Replace it with the client's own preview slug.")
            elif _looks_like_a_placeholder(slug):
                self.add("W-SLUG-PLACEHOLDER", WARNING,
                         "The loader %s has slug %r, which looks like the placeholder "
                         "from the example profile rather than a real property slug on "
                         "the target site. The editor preview will resolve nothing."
                         % (widget.id, slug), element=widget, control="slug")
            elif self.profile.preview_slug and slug != self.profile.preview_slug:
                self.add("W-SLUG-MISMATCH", WARNING,
                         "The loader %s uses slug %r while the target profile declares "
                         "%r." % (widget.id, slug, self.profile.preview_slug),
                         element=widget, control="slug")

    def _check_secret(self, element, key, value):
        for text in _strings_in(value):
            for label, pattern in _SECRET_PATTERNS:
                if pattern.search(text):
                    self.add("E-SECRET", ERROR,
                             "%s setting %r contains something shaped like a %s. "
                             "Credentials must never travel inside a template."
                             % (element.id, key, label),
                             element=element, control=key,
                             hint="Remove the value; the finding deliberately does not "
                                  "quote it.")
                    return

    def _check_frozen_literal(self, element, key, value):
        literals = self.profile.forbidden_literals
        if not literals:
            return
        placeholders = self.cat.placeholder_values
        for text in _strings_in(value):
            if text in placeholders:
                continue
            for literal in literals:
                if literal and literal in text:
                    self.add("E-FROZEN-CONTENT", ERROR,
                             "%s setting %r contains %r, which the target profile lists "
                             "as content that must not be frozen into the template. "
                             "Property facts belong in the API data, bound through the "
                             "crecs-property tag." % (element.id, key, literal),
                             element=element, control=key)
                    return

    def _check_asset(self, element, key, value):
        allowed = self.profile.allowed_hosts()
        for text in _strings_in(value):
            if not text.startswith(("http://", "https://")):
                continue
            host = text.split("//", 1)[1].split("/", 1)[0].split(":")[0]
            if allowed and host in allowed:
                continue
            self.add("W-CROSS-SITE-ASSET", WARNING,
                     "%s setting %r points at %s. On another site that either loads "
                     "from the original host or breaks."
                     % (element.id, key, host),
                     element=element, control=key)
            media_id = value.get("id") if isinstance(value, dict) else None
            if media_id is not None and not self.profile.knows_media(media_id):
                self.add("E-DEP-UNRESOLVED", ERROR,
                         "%s setting %r references attachment id %s on %s. Attachment "
                         "ids are per-site; reusing one by assumption points at "
                         "whatever happens to have that id on the target."
                         % (element.id, key, media_id, host),
                         element=element, control=key,
                         hint='Declare it in the profile\'s "media" map once the asset '
                              'exists on the client site, or clear the setting.')
            return


def _strings_in(value, depth=0):
    if depth > 6:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            for text in _strings_in(item, depth + 1):
                yield text
    elif isinstance(value, list):
        for item in value:
            for text in _strings_in(item, depth + 1):
                yield text


def _describe(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "the boolean %s" % ("true" if value else "false")
    if isinstance(value, str):
        return "the string %r" % (value[:40],)
    if isinstance(value, (int, float)):
        return "the number %r" % value
    if isinstance(value, list):
        return "an array of %d item(s)" % len(value)
    if isinstance(value, dict):
        return "an object with keys %s" % ", ".join(sorted(value)[:5])
    return type(value).__name__


def _describe_condition(dep_key, expected):
    negate = dep_key.endswith("!")
    name = dep_key[:-1] if negate else dep_key
    values = expected if isinstance(expected, list) else [expected]
    joined = " or ".join(repr(v) for v in values)
    return "%s is %s%s" % (name, "not " if negate else "", joined)


_PLACEHOLDER_WORDS = ("replace", "your-", "example", "changeme", "todo", "xxx",
                      "placeholder", "some-slug")


def _looks_like_a_placeholder(text):
    lowered = str(text).lower()
    return any(word in lowered for word in _PLACEHOLDER_WORDS)


def _is_numeric(text):
    try:
        float(text)
        return True
    except (TypeError, ValueError):
        return False


def validate(document, catalog, profile, baseline_keys=None):
    run = _Run(document, catalog, profile, baseline_keys)
    run.check_envelope_strings()
    run.check_envelope()
    run.check_element_model()
    run.check_ids()
    run.check_nesting()
    run.check_loader_and_cardinality()
    run.check_settings()
    run.check_bindings()
    run.check_loader_slug()
    run.check_profile_popups()
    run.check_coverage()

    widgets = document.widgets()
    summary = {
        "elements": len(document.elements()),
        "widgets": len(widgets),
        "crecs_widgets": sorted({w.widget_type for w in widgets
                                 if catalog.is_crecs_widget(w.widget_type or "")}),
        "other_widgets": sorted({w.widget_type for w in widgets
                                 if not catalog.is_crecs_widget(w.widget_type or "")}),
        "bound_params": sorted(run.bound_params),
        "element_model": document.element_model(),
        "export_version": document.export_version,
        "profile": profile.describe() if not profile.is_empty() else None,
        "catalog": catalog.fingerprint(),
    }
    order = {ERROR: 0, WARNING: 1, INFO: 2}
    findings = sorted(run.findings, key=lambda f: (order[f.severity], f.code,
                                                   f.element_id or ""))
    return Result(findings, summary)
