"""Shared test helpers."""

import copy


_MINIMAL = {
    "content": [
        {
            "id": "1000001",
            "elType": "section",
            "isInner": False,
            "settings": {"_title": "Property Data"},
            "elements": [
                {
                    "id": "1000002",
                    "elType": "column",
                    "isInner": False,
                    "settings": {"_column_size": 100},
                    "elements": [
                        {
                            "id": "1000003",
                            "elType": "widget",
                            "widgetType": "crecs_property_data",
                            "isInner": False,
                            "settings": {"slug": "a-real-slug"},
                            "elements": [],
                        },
                        {
                            "id": "1000004",
                            "elType": "widget",
                            "widgetType": "heading",
                            "isInner": False,
                            "settings": {"title": "Add Your Heading Text Here"},
                            "elements": [],
                        },
                        {
                            "id": "1000005",
                            "elType": "widget",
                            "widgetType": "crecs_property_fields",
                            "isInner": False,
                            "settings": {"layout_type": "two_column"},
                            "elements": [],
                        },
                        {
                            "id": "1000006",
                            "elType": "widget",
                            "widgetType": "crecs_property_docs",
                            "isInner": False,
                            "settings": {"widget_title": "Investor Documents"},
                            "elements": [],
                        },
                        {
                            "id": "1000008",
                            "elType": "widget",
                            "widgetType": "crecs_property_suites",
                            "isInner": False,
                            "settings": {"layout_type": "table"},
                            "elements": [],
                        },
                        {
                            "id": "1000007",
                            "elType": "widget",
                            "widgetType": "button",
                            "isInner": False,
                            "settings": {"text": "Download flyer"},
                            "elements": [],
                        },
                    ],
                }
            ],
        }
    ],
    "page_settings": [],
    "version": "0.4",
    "title": "Test fixture",
    "type": "page",
}


def minimal_envelope():
    """A small but structurally valid document: loader first, a heading, two CRECS
    widgets and a button. Deliberately incomplete on coverage, so the coverage
    warning fires."""
    return copy.deepcopy(_MINIMAL)


def _walk(node):
    yield node
    for child in node.get("elements", []) or []:
        for item in _walk(child):
            yield item


def find(envelope, widget_type=None, el_type=None, **kwargs):
    """Return the first raw element dict matching the given criteria.

    ``widget_type`` may be given positionally or as a keyword; passing None with an
    ``el_type`` matches on the element type alone.
    """
    if "widget_type" in kwargs:
        widget_type = kwargs.pop("widget_type")
    if kwargs:
        raise TypeError("unexpected keyword(s): %s" % ", ".join(kwargs))
    if widget_type is None and el_type is None:
        raise TypeError("find() needs widget_type, el_type, or both")

    roots = envelope["content"] if isinstance(envelope, dict) else envelope
    for root in roots:
        for node in _walk(root):
            if el_type and node.get("elType") != el_type:
                continue
            if widget_type is not None and node.get("widgetType") != widget_type:
                continue
            return node
    raise AssertionError(
        "no element matching widget_type=%r el_type=%r" % (widget_type, el_type)
    )


def codes(result):
    return [f.code for f in result.findings]


def severity_of(result, code):
    for finding in result.findings:
        if finding.code == code:
            return finding.severity
    return None
