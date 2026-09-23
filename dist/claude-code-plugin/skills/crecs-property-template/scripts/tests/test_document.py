"""Contract for the Elementor document model.

The model must preserve everything it does not understand, keep element ids stable,
and never coerce a value's JSON type. Empty string, 0, null, [] and {} are five
different things and all five have to survive a load/save round trip.
"""

import copy
import json
import unittest

from crecs.document import Document, DocumentError


ENVELOPE = {
    "content": [
        {
            "id": "1111111",
            "elType": "section",
            "isInner": False,
            "settings": {"_title": "Property Data"},
            "elements": [
                {
                    "id": "2222222",
                    "elType": "column",
                    "isInner": False,
                    "settings": {"_column_size": 100},
                    "elements": [
                        {
                            "id": "3333333",
                            "elType": "widget",
                            "widgetType": "crecs_property_data",
                            "isInner": False,
                            "settings": {"slug": "example-slug"},
                            "elements": [],
                        }
                    ],
                }
            ],
        }
    ],
    "page_settings": [],
    "version": "0.4",
    "title": "Fixture",
    "type": "page",
}


def doc():
    return Document(copy.deepcopy(ENVELOPE))


class TestLoad(unittest.TestCase):
    def test_accepts_the_reference_envelope(self):
        d = doc()
        self.assertEqual(d.export_version, "0.4")
        self.assertEqual(d.doc_type, "page")

    def test_accepts_a_bare_content_array(self):
        d = Document(copy.deepcopy(ENVELOPE["content"]))
        self.assertEqual(len(d.roots), 1)
        self.assertIsNone(d.export_version)

    def test_rejects_a_non_list_content(self):
        with self.assertRaises(DocumentError):
            Document({"content": {"nope": 1}})

    def test_rejects_an_element_without_eltype(self):
        broken = copy.deepcopy(ENVELOPE)
        del broken["content"][0]["elType"]
        with self.assertRaises(DocumentError):
            Document(broken)


class TestWalk(unittest.TestCase):
    def test_finds_every_element(self):
        self.assertEqual(len(doc().elements()), 3)

    def test_lookup_by_id(self):
        self.assertEqual(doc().by_id("3333333").widget_type, "crecs_property_data")

    def test_unknown_id_raises_with_an_actionable_message(self):
        with self.assertRaises(DocumentError) as cm:
            doc().by_id("nope")
        self.assertIn("nope", str(cm.exception))

    def test_widget_order_is_document_order(self):
        self.assertEqual([w.widget_type for w in doc().widgets()],
                         ["crecs_property_data"])

    def test_parent_and_path_are_available(self):
        d = doc()
        el = d.by_id("3333333")
        self.assertEqual(d.parent_of(el).id, "2222222")
        self.assertIn("crecs_property_data", d.path_of(el))


class TestTypePreservation(unittest.TestCase):
    def test_all_five_empty_shapes_survive(self):
        d = doc()
        d.set_setting("3333333", "a_string", "")
        d.set_setting("3333333", "a_zero", 0)
        d.set_setting("3333333", "a_null", None)
        d.set_setting("3333333", "a_list", [])
        d.set_setting("3333333", "a_map", {})
        again = Document(json.loads(json.dumps(d.to_envelope())))
        s = again.by_id("3333333").settings
        self.assertEqual(s["a_string"], "")
        self.assertEqual(s["a_zero"], 0)
        self.assertIsNone(s["a_null"])
        self.assertEqual(s["a_list"], [])
        self.assertEqual(s["a_map"], {})
        self.assertIsInstance(s["a_zero"], int)
        self.assertNotIsInstance(s["a_zero"], bool)

    def test_false_is_not_confused_with_empty_string(self):
        d = doc()
        d.set_setting("3333333", "flag", False)
        self.assertIs(d.by_id("3333333").settings["flag"], False)

    def test_unknown_keys_are_preserved_verbatim(self):
        src = copy.deepcopy(ENVELOPE)
        src["content"][0]["settings"]["section_background_image"] = {
            "id": "5850", "url": "https://example.test/x.png"
        }
        d = Document(src)
        d.set_setting("3333333", "slug", "other")
        out = d.to_envelope()
        self.assertEqual(
            out["content"][0]["settings"]["section_background_image"]["id"], "5850"
        )


class TestEdit(unittest.TestCase):
    def test_set_and_unset(self):
        d = doc()
        d.set_setting("3333333", "slug", "abc")
        self.assertEqual(d.by_id("3333333").settings["slug"], "abc")
        d.unset_setting("3333333", "slug")
        self.assertNotIn("slug", d.by_id("3333333").settings)

    def test_unset_of_an_absent_key_is_an_error_not_a_silent_noop(self):
        with self.assertRaises(DocumentError):
            doc().unset_setting("3333333", "not_there")

    def test_add_widget_generates_a_unique_id(self):
        d = doc()
        new_id = d.add_widget("2222222", "crecs_property_rates", {"property_rate": "rate_1"})
        self.assertRegex(new_id, r"^[0-9a-f]{7,8}$")
        self.assertEqual(len(d.elements()), 4)
        self.assertNotIn(new_id, {"1111111", "2222222", "3333333"})

    def test_add_widget_respects_an_explicit_index(self):
        d = doc()
        first = d.add_widget("2222222", "crecs_property_rates", {}, index=0)
        self.assertEqual(d.by_id("2222222").children[0].id, first)

    def test_add_widget_into_a_widget_is_refused(self):
        with self.assertRaises(DocumentError):
            doc().add_widget("3333333", "crecs_property_rates", {})

    def test_remove_returns_the_removed_subtree(self):
        d = doc()
        removed = d.remove("3333333")
        self.assertEqual(removed["widgetType"], "crecs_property_data")
        self.assertEqual(len(d.elements()), 2)

    def test_move_preserves_the_element_id(self):
        d = doc()
        extra_col = d.add_column("1111111")
        d.move("3333333", into=extra_col)
        self.assertEqual(d.by_id("3333333").widget_type, "crecs_property_data")
        self.assertEqual(d.parent_of(d.by_id("3333333")).id, extra_col)

    def test_move_after_reorders_within_a_parent(self):
        d = doc()
        second = d.add_widget("2222222", "crecs_property_rates", {})
        d.move("3333333", after=second)
        self.assertEqual([c.id for c in d.by_id("2222222").children], [second, "3333333"])

    def test_move_into_own_descendant_is_refused(self):
        d = doc()
        with self.assertRaises(DocumentError):
            d.move("1111111", into="2222222")


class TestIds(unittest.TestCase):
    def test_duplicate_ids_are_detected(self):
        src = copy.deepcopy(ENVELOPE)
        src["content"][0]["elements"][0]["elements"][0]["id"] = "2222222"
        d = Document(src)
        self.assertEqual(d.duplicate_ids(), ["2222222"])

    def test_no_duplicates_in_the_fixture(self):
        self.assertEqual(doc().duplicate_ids(), [])

    def test_malformed_ids_are_reported(self):
        src = copy.deepcopy(ENVELOPE)
        src["content"][0]["id"] = "NOT-HEX"
        self.assertEqual(Document(src).malformed_ids(), ["NOT-HEX"])


class TestElementModel(unittest.TestCase):
    def test_reports_classic_sections(self):
        self.assertEqual(doc().element_model(), "classic")

    def test_reports_containers_when_present(self):
        src = copy.deepcopy(ENVELOPE)
        src["content"] = [{"id": "9999999", "elType": "container", "settings": {},
                           "elements": []}]
        self.assertEqual(Document(src).element_model(), "container")


if __name__ == "__main__":
    unittest.main()
