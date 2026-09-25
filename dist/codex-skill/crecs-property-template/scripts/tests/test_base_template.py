"""Properties of the shipped base template itself.

Until 2026-09-25 the only guard on these lived in the plugin repository — case C-05 of
`tools/defect-tests/run.php` ran the plugin's preview validator over this file. When the
skill moved to its own repository that guard stayed behind, and nothing here checked the
template the skill ships to every client. These bring it home, against the skill's own
validator.

How they are built is the point. The first version asserted "no finding with code X" for
four codes — and all four were the *plugin's* names (W-FOREIGN-CONTROL, E-NO-CONTROL,
E-LOADER-NOT-FIRST, E-DUPLICATE-ID). None exists in this validator, which names the same
things E-CONTROL-UNKNOWN, E-LOADER-ORDER and E-ID-DUPLICATE. An assertion that a code
nobody emits is absent passes forever. It was caught only by injecting the defect and
watching the test stay green.

So every case now does both halves: it breaks a copy of the template and requires the
finding to appear, and only then requires the shipped template to be free of it. A case
whose code drifts out of the validator fails the first half instead of passing silently.
"""

import copy
import json
import os
import unittest

from crecs import validate
from crecs.catalog import Catalog
from crecs.document import Document
from crecs.profile import Profile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(SKILL_ROOT, "assets", "property-template-all-widgets.json")
CATALOG = Catalog.load_default()


def shipped():
    with open(BASE, encoding="utf-8") as fh:
        return json.load(fh)


def codes_in(payload):
    result = validate.validate(Document(payload), CATALOG, Profile.empty())
    return [f.code for f in result.findings]


def walk(nodes):
    for n in nodes:
        yield n
        yield from walk(n.get("elements", []))


def first_of(payload, predicate):
    return next(n for n in walk(payload["content"]) if predicate(n))


# -- the defects, each applied to a copy -----------------------------------------------

def inject_foreign_control(payload):
    # What C-05 was written for: content_width on a column, where it is not a control
    # and Elementor ignores it.
    column = first_of(payload, lambda n: n.get("elType") == "column")
    column.setdefault("settings", {})["content_width"] = {"unit": "px", "size": 100}


def move_loader_out_of_first_place(payload):
    # The loader has to render before every widget that reads the property it loads.
    first_section = payload["content"].pop(0)
    payload["content"].append(first_section)


def duplicate_an_id(payload):
    elements = list(walk(payload["content"]))
    elements[1]["id"] = elements[0]["id"]


def remove_the_loader(payload):
    def strip(nodes):
        nodes[:] = [n for n in nodes if n.get("widgetType") != "crecs_property_data"]
        for n in nodes:
            strip(n.get("elements", []))
    strip(payload["content"])


CASES = [
    ("E-CONTROL-UNKNOWN", inject_foreign_control,
     "a control registered on another element type, inert here"),
    ("E-LOADER-ORDER", move_loader_out_of_first_place,
     "the loader must come first in document order"),
    ("E-ID-DUPLICATE", duplicate_an_id,
     "two elements sharing an id"),
    ("E-LOADER-MISSING", remove_the_loader,
     "no loader, so no widget has a property to read"),
]


class BaseTemplate(unittest.TestCase):
    def test_each_check_can_actually_fail(self):
        # The half that the first version was missing.
        for code, breaker, why in CASES:
            with self.subTest(code=code):
                broken = copy.deepcopy(shipped())
                breaker(broken)
                # assertTrue rather than assertIn: the latter prints every one of the
                # template's several hundred findings, burying the one line that matters.
                self.assertTrue(
                    code in codes_in(broken),
                    "injecting '%s' did not produce %s — the code has drifted, or the "
                    "check is not wired, and the case below proves nothing" % (why, code),
                )

    def test_the_shipped_template_is_free_of_each(self):
        found = codes_in(shipped())
        for code, _, why in CASES:
            with self.subTest(code=code):
                self.assertNotIn(code, found, "the shipped base template has " + why)


if __name__ == "__main__":
    unittest.main()
