"""Contract for the dynamic-tag binding parser.

Bindings must be read structurally: scan the shortcode's attributes, URL-decode the
settings payload, JSON-parse it, then check its shape. A single regex over the whole
string is explicitly not acceptable, because a corrupted payload has to be
distinguishable from a valid one and from a payload whose shape is wrong.
"""

import unittest

from crecs import bindings


VALID = (
    '[elementor-tag id="c9ca4f5" name="crecs-property" '
    'settings="%7B%22param_name%22%3A%22property_name%22%7D"]'
)
VALID_POPUP = (
    '[elementor-tag id="a231826" name="popup" settings="%7B%22popup%22%3A%224554%22%7D"]'
)


class TestParse(unittest.TestCase):
    def test_parses_a_valid_crecs_binding(self):
        tag = bindings.parse_tag(VALID)
        self.assertEqual(tag.instance_id, "c9ca4f5")
        self.assertEqual(tag.name, "crecs-property")
        self.assertEqual(tag.settings, {"param_name": "property_name"})
        self.assertIsNone(tag.error)

    def test_parses_a_pro_popup_binding(self):
        tag = bindings.parse_tag(VALID_POPUP)
        self.assertEqual(tag.name, "popup")
        self.assertEqual(tag.settings, {"popup": "4554"})
        self.assertIsNone(tag.error)

    def test_attribute_order_does_not_matter(self):
        shuffled = (
            '[elementor-tag settings="%7B%22param_name%22%3A%22property_type%22%7D" '
            'name="crecs-property" id="b2cfd53"]'
        )
        tag = bindings.parse_tag(shuffled)
        self.assertEqual(tag.name, "crecs-property")
        self.assertEqual(tag.settings, {"param_name": "property_type"})

    def test_missing_settings_attribute_yields_empty_settings_not_an_error(self):
        tag = bindings.parse_tag('[elementor-tag id="abc1234" name="crecs-property"]')
        self.assertEqual(tag.settings, {})
        self.assertIsNone(tag.error)

    def test_single_quoted_attributes_are_accepted(self):
        tag = bindings.parse_tag(
            "[elementor-tag id='c9ca4f5' name='crecs-property' "
            "settings='%7B%22param_name%22%3A%22property_name%22%7D']"
        )
        self.assertEqual(tag.settings, {"param_name": "property_name"})


class TestCorruption(unittest.TestCase):
    def test_not_a_shortcode(self):
        tag = bindings.parse_tag("property_name")
        self.assertIsNotNone(tag.error)
        self.assertIn("not an elementor-tag", tag.error)

    def test_unterminated_shortcode(self):
        tag = bindings.parse_tag('[elementor-tag id="c9ca4f5" name="crecs-property"')
        self.assertIsNotNone(tag.error)

    def test_missing_name_attribute(self):
        tag = bindings.parse_tag('[elementor-tag id="c9ca4f5" settings="%7B%7D"]')
        self.assertIsNotNone(tag.error)
        self.assertIn("name", tag.error)

    def test_settings_not_valid_json_after_decoding(self):
        tag = bindings.parse_tag(
            '[elementor-tag id="c9ca4f5" name="crecs-property" settings="%7Bnope"]'
        )
        self.assertIsNotNone(tag.error)
        self.assertIn("JSON", tag.error)

    def test_settings_json_is_not_an_object(self):
        # "%5B1%5D" -> [1]
        tag = bindings.parse_tag(
            '[elementor-tag id="c9ca4f5" name="crecs-property" settings="%5B1%5D"]'
        )
        self.assertIsNotNone(tag.error)
        self.assertIn("object", tag.error)

    def test_double_encoded_payload_is_reported_not_silently_accepted(self):
        tag = bindings.parse_tag(
            '[elementor-tag id="c9ca4f5" name="crecs-property" '
            'settings="%2525 7B%22param_name%22%7D"]'
        )
        self.assertIsNotNone(tag.error)

    def test_instance_id_shape_is_reported(self):
        tag = bindings.parse_tag(
            '[elementor-tag id="NOT-HEX!" name="crecs-property" settings="%7B%7D"]'
        )
        self.assertIsNotNone(tag.error)
        self.assertIn("id", tag.error)


class TestBuild(unittest.TestCase):
    def test_round_trip(self):
        built = bindings.build_tag("crecs-property", {"param_name": "property_name"},
                                   instance_id="c9ca4f5")
        self.assertEqual(bindings.parse_tag(built).settings,
                         {"param_name": "property_name"})

    def test_generated_instance_id_is_accepted_by_the_parser(self):
        built = bindings.build_tag("crecs-property", {"param_name": "flyer_url"})
        tag = bindings.parse_tag(built)
        self.assertIsNone(tag.error)
        self.assertEqual(tag.settings, {"param_name": "flyer_url"})
        self.assertRegex(tag.instance_id, r"^[0-9a-f]{7,8}$")

    def test_build_rejects_a_non_object_payload(self):
        with self.assertRaises(ValueError):
            bindings.build_tag("crecs-property", ["property_name"])


class TestDynamicMap(unittest.TestCase):
    def test_reads_every_binding_of_an_element(self):
        settings = {
            "title": "Add Your Heading Text Here",
            "__dynamic__": {"title": VALID},
        }
        found = bindings.read_element_bindings(settings)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].control, "title")
        self.assertEqual(found[0].tag.name, "crecs-property")

    def test_absent_dynamic_map_yields_nothing(self):
        self.assertEqual(bindings.read_element_bindings({"title": "x"}), [])

    def test_dynamic_map_of_the_wrong_type_is_reported(self):
        found = bindings.read_element_bindings({"__dynamic__": "oops"})
        self.assertEqual(len(found), 1)
        self.assertIsNotNone(found[0].error)


if __name__ == "__main__":
    unittest.main()


class EmptyDynamicMap(unittest.TestCase):
    """Elementor writes `"__dynamic__": []` when an element has no bindings left.

    That is not corruption, it is how PHP's json_encode renders an empty associative
    array, and Elementor leaves one behind whenever the last dynamic binding on an
    element is removed. Two buttons on a real client template arrived that way and the
    export was refused with E-BINDING-CORRUPT — a document the site itself had just
    produced, called unreadable.

    An empty *object* has always been accepted. Only the list form was not.
    """

    def test_an_empty_list_means_no_bindings(self):
        self.assertEqual([], bindings.read_element_bindings({"__dynamic__": []}))

    def test_an_empty_object_still_means_no_bindings(self):
        self.assertEqual([], bindings.read_element_bindings({"__dynamic__": {}}))

    def test_a_non_empty_list_is_still_corrupt(self):
        # A list with something in it is not Elementor's empty marker; it is a document
        # nobody can read, and saying so is the point of the check.
        found = bindings.read_element_bindings({"__dynamic__": ["[elementor-tag /]"]})
        self.assertEqual(1, len(found))
        self.assertIsNotNone(found[0].error)

    def test_a_string_is_still_corrupt(self):
        found = bindings.read_element_bindings({"__dynamic__": "nope"})
        self.assertEqual(1, len(found))
        self.assertIsNotNone(found[0].error)
