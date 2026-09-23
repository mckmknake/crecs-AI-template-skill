"""Coverage reporting.

Two questions, answered honestly:

* which relevant widgets appear in the shipped base template or a fixture, and
* which control families actually pass through the validator's value checks when the
  suite runs.

A family counts as exercised when at least one of its controls carries a value in the
base template or a fixture, because validating those documents runs every value check
for that control type. Families with no such control are reported as **not
exercised** rather than quietly assumed to work.
"""

import json
import os

from .document import Document

_HERE = os.path.dirname(os.path.abspath(__file__))
_SKILL_ROOT = os.path.dirname(os.path.dirname(_HERE))
ASSETS = os.path.join(_SKILL_ROOT, "assets")
BASE_TEMPLATE = os.path.join(ASSETS, "property-template-all-widgets.json")
FIXTURES = os.path.join(ASSETS, "fixtures")

# Control-name families, matched on the part after the last underscore group. These
# are the groups Elementor itself uses, so "exercised" means something concrete.
FAMILIES = {
    "typography": lambda name, c: "_typography" in name or c.type == "font",
    "border": lambda name, c: "_border" in name,
    "box_shadow": lambda name, c: "box_shadow" in name or c.type == "box_shadow",
    "text_shadow": lambda name, c: "text_shadow" in name or c.type == "text_shadow",
    "dimensions": lambda name, c: c.type == "dimensions",
    "color": lambda name, c: c.type == "color",
    "slider": lambda name, c: c.type == "slider",
    "select": lambda name, c: c.type in ("select", "select2"),
    "switcher": lambda name, c: c.type == "switcher",
    "choose": lambda name, c: c.type == "choose",
    "number": lambda name, c: c.type == "number",
    "text": lambda name, c: c.type in ("text", "textarea", "wysiwyg"),
    "media": lambda name, c: c.type in ("media", "gallery"),
    "url": lambda name, c: c.type == "url",
    "repeater": lambda name, c: c.type == "repeater",
    "popover_toggle": lambda name, c: c.type == "popover_toggle",
}


def _load(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        try:
            return Document(json.load(fh))
        except Exception:
            return None


def _documents():
    docs = []
    base = _load(BASE_TEMPLATE)
    if base is not None:
        docs.append(("base", base))
    if os.path.isdir(FIXTURES):
        for name in sorted(os.listdir(FIXTURES)):
            if not name.endswith(".json"):
                continue
            doc = _load(os.path.join(FIXTURES, name))
            if doc is not None:
                docs.append((name, doc))
    return docs


def report(catalog):
    docs = _documents()

    present_widgets = set()
    used_keys = {}
    for _, doc in docs:
        for widget in doc.widgets():
            if widget.widget_type:
                present_widgets.add(widget.widget_type)
                used_keys.setdefault(widget.widget_type, set()).update(
                    k for k in widget.settings if k != "__dynamic__"
                )

    relevant = [n for n in catalog.relevant_widget_names()
                if catalog.relevance(n) in ("required", "core", "non_visual",
                                            "conditional")]
    covered = [n for n in relevant if n in present_widgets]
    uncovered = [n for n in relevant if n not in present_widgets]

    exercised = set()
    for widget_type, keys in used_keys.items():
        if not catalog.is_crecs_widget(widget_type):
            continue
        for key in keys:
            base_name, _ = catalog.split_device_suffix(key)
            control = catalog.control(widget_type, base_name)
            if control is None:
                continue
            for family, matches in FAMILIES.items():
                try:
                    if matches(base_name, control):
                        exercised.add(family)
                except Exception:  # pragma: no cover - defensive
                    continue

    # A family only counts as "available" when some relevant widget declares it.
    available = set()
    for widget_type in relevant:
        for name, control in catalog.controls(widget_type).items():
            for family, matches in FAMILIES.items():
                try:
                    if matches(name, control):
                        available.add(family)
                except Exception:  # pragma: no cover
                    continue

    not_exercised = sorted(available - exercised)

    per_widget = {}
    for widget_type in relevant:
        declared = set(catalog.controls(widget_type))
        touched = {catalog.split_device_suffix(k)[0]
                   for k in used_keys.get(widget_type, set())}
        touched &= declared
        per_widget[widget_type] = {
            "in_documents": widget_type in present_widgets,
            "controls_declared": len(declared),
            "controls_with_a_value": len(touched),
        }

    return {
        "documents_examined": [name for name, _ in docs],
        "widgets_relevant": len(relevant),
        "widgets_covered": len(covered),
        "widgets_uncovered": uncovered,
        "families_total": len(available),
        "families_exercised": len(sorted(available & exercised)),
        "families_exercised_names": sorted(available & exercised),
        "families_not_exercised": not_exercised,
        "per_widget": per_widget,
        "method": ("A widget counts as covered when it appears in the shipped base "
                   "template or a fixture. A control family counts as exercised when "
                   "at least one control of that family carries a value in those "
                   "documents, so validating them runs that family's value checks. "
                   "Controls with no value in any document are NOT exercised."),
        "claim_level": ("tested in the harness; no template was imported into "
                        "Elementor and nothing was rendered"),
    }
