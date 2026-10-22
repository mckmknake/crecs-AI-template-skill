"""Contract for the validator.

Severities: ERROR blocks a "ready" export; WARNING and INFO do not.

Two rules run through everything here:

* a *newly introduced* setting with no confirmed contract is an ERROR, while a
  *pre-existing* unknown setting is preserved and reported as a WARNING;
* a visual preference is never reported as a technical restriction.
"""

import copy
import unittest

from crecs import validate
from crecs.catalog import Catalog
from crecs.document import Document
from crecs.profile import Profile

from tests.helpers import minimal_envelope, find, codes, severity_of


CATALOG = Catalog.load_default()


def run(envelope, profile=None, baseline_keys=None):
    return validate.validate(
        Document(copy.deepcopy(envelope)),
        CATALOG,
        profile=profile or Profile.empty(),
        baseline_keys=baseline_keys or set(),
    )


class TestEnvelope(unittest.TestCase):
    def test_reference_envelope_passes(self):
        self.assertNotIn("E-ENVELOPE-VERSION", codes(run(minimal_envelope())))

    def test_unsupported_export_version_is_an_error(self):
        env = minimal_envelope()
        env["version"] = "99.0"
        self.assertIn("E-ENVELOPE-VERSION", codes(run(env)))

    def test_missing_type_is_a_warning_not_an_error(self):
        env = minimal_envelope()
        del env["type"]
        self.assertEqual(severity_of(run(env), "W-ENVELOPE-TYPE"), "WARNING")

    def test_container_element_model_is_an_error(self):
        env = minimal_envelope()
        env["content"].append(
            {"id": "9999999", "elType": "container", "settings": {}, "elements": []}
        )
        self.assertIn("E-ELEMENT-MODEL", codes(run(env)))


class TestIds(unittest.TestCase):
    def test_duplicate_element_id_is_an_error(self):
        env = minimal_envelope()
        env["content"][0]["elements"][0]["id"] = env["content"][0]["id"]
        self.assertIn("E-ID-DUPLICATE", codes(run(env)))

    def test_malformed_element_id_is_an_error(self):
        env = minimal_envelope()
        env["content"][0]["id"] = "Section-One"
        self.assertIn("E-ID-MALFORMED", codes(run(env)))


class TestNesting(unittest.TestCase):
    def test_widget_with_children_is_an_error(self):
        env = minimal_envelope()
        loader = find(env, "crecs_property_data")
        loader["elements"] = [
            {"id": "8888888", "elType": "widget", "widgetType": "crecs_property_rates",
             "settings": {}, "elements": []}
        ]
        self.assertIn("E-NESTING", codes(run(env)))

    def test_widget_directly_under_a_section_is_an_error(self):
        env = minimal_envelope()
        env["content"][0]["elements"].append(
            {"id": "7777777", "elType": "widget", "widgetType": "crecs_property_rates",
             "settings": {}, "elements": []}
        )
        self.assertIn("E-NESTING", codes(run(env)))

    def test_column_outside_a_section_is_an_error(self):
        env = minimal_envelope()
        env["content"].append(
            {"id": "6666666", "elType": "column", "settings": {}, "elements": []}
        )
        self.assertIn("E-NESTING", codes(run(env)))


class TestControls(unittest.TestCase):
    def test_a_registered_control_passes(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["layout_type"] = "two_column"
        self.assertNotIn("E-CONTROL-UNKNOWN", codes(run(env)))
        self.assertNotIn("E-CONTROL-OPTION", codes(run(env)))

    def test_an_invented_control_key_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_glow_intensity"] = 5
        result = run(env)
        self.assertIn("E-CONTROL-UNKNOWN", codes(result))
        item = [f for f in result.findings if f.code == "E-CONTROL-UNKNOWN"][0]
        self.assertIn("card_glow_intensity", item.message)

    def test_a_preexisting_unknown_key_is_only_a_warning(self):
        env = minimal_envelope()
        widget = find(env, "crecs_property_fields")
        widget["settings"]["section_background_image"] = {"id": "5850"}
        baseline = {widget["id"] + "::section_background_image"}
        result = run(env, baseline_keys=baseline)
        self.assertNotIn("E-CONTROL-UNKNOWN", codes(result))
        self.assertEqual(severity_of(result, "W-KEY-PREEXISTING-UNKNOWN"), "WARNING")

    def test_a_known_legacy_alias_reports_the_current_name(self):
        env = minimal_envelope()
        widget = find(env, "crecs_property_fields")
        widget["settings"]["label_typography_font_size"] = {"unit": "px", "size": 16, "sizes": []}
        result = run(env, baseline_keys={widget["id"] + "::label_typography_font_size"})
        item = [f for f in result.findings if f.code == "W-LEGACY-ALIAS"][0]
        self.assertIn("field_label_typography_font_size", item.message)

    def test_a_value_outside_a_closed_vocabulary_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["layout_type"] = "three_column"
        self.assertIn("E-CONTROL-OPTION", codes(run(env)))

    def test_an_open_vocabulary_value_is_accepted_and_reported_as_info(self):
        env = minimal_envelope()
        find(env, "crecs_property_docs")["settings"]["popup_template"] = "99999"
        result = run(env)
        self.assertNotIn("E-CONTROL-OPTION", codes(result))
        self.assertEqual(severity_of(result, "I-OPEN-VOCABULARY"), "INFO")

    def test_wrong_value_shape_for_a_dimensions_control_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_margin"] = "10px"
        self.assertIn("E-CONTROL-TYPE", codes(run(env)))

    def test_correct_dimensions_shape_passes(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_margin"] = {
            "unit": "px", "top": "10", "right": "10", "bottom": "10", "left": "10",
            "isLinked": True,
        }
        self.assertNotIn("E-CONTROL-TYPE", codes(run(env)))

    def test_a_unit_outside_size_units_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_margin"] = {
            "unit": "parsec", "top": "1", "right": "1", "bottom": "1", "left": "1",
            "isLinked": True,
        }
        self.assertIn("E-CONTROL-UNIT", codes(run(env)))

    def test_switcher_accepts_its_return_value_and_empty_string(self):
        env = minimal_envelope()
        for value in ("yes", ""):
            find(env, "crecs_property_fields")["settings"]["show_label"] = value
            self.assertNotIn("E-CONTROL-TYPE", codes(run(env)), value)

    def test_switcher_rejects_a_boolean(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["show_label"] = True
        self.assertIn("E-CONTROL-TYPE", codes(run(env)))

    def test_a_control_whose_condition_is_unmet_is_reported_as_info(self):
        env = minimal_envelope()
        widget = find(env, "crecs_property_fields")
        widget["settings"]["layout_type"] = "list"
        widget["settings"]["first_column_alignment"] = "center"
        self.assertEqual(severity_of(run(env), "I-CONDITION-UNMET"), "INFO")

    def test_core_widget_controls_are_validated_too(self):
        """Delivery 2 catalogued the Elementor core widgets a property template uses,
        so a heading is checked like any CRECS widget rather than waved through."""
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["title_color"] = "#ffffff"
        self.assertNotIn("E-CONTROL-UNKNOWN", codes(run(env)))
        heading["settings"]["title_glow"] = "#ffffff"
        self.assertIn("E-CONTROL-UNKNOWN", codes(run(env)))


class TestResponsive(unittest.TestCase):
    def test_device_variant_of_a_responsive_control_passes(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_margin_mobile"] = {
            "unit": "px", "top": "5", "right": "5", "bottom": "5", "left": "5",
            "isLinked": True,
        }
        self.assertNotIn("E-RESPONSIVE-UNSUPPORTED", codes(run(env)))

    def test_device_variant_of_a_non_responsive_control_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_color_mobile"] = "#fff"
        self.assertIn("E-RESPONSIVE-UNSUPPORTED", codes(run(env)))

    def test_an_inactive_breakpoint_suffix_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_margin_widescreen"] = {
            "unit": "px", "top": "5", "right": "5", "bottom": "5", "left": "5",
            "isLinked": True,
        }
        self.assertIn("E-RESPONSIVE-DEVICE", codes(run(env)))


class TestLoaderAndCardinality(unittest.TestCase):
    def test_missing_loader_is_an_error(self):
        env = minimal_envelope()
        loader = find(env, "crecs_property_data")
        parent = find(env, el_type="column")
        parent["elements"] = [e for e in parent["elements"] if e is not loader]
        self.assertIn("E-LOADER-MISSING", codes(run(env)))

    def test_loader_not_first_is_an_error(self):
        env = minimal_envelope()
        column = find(env, el_type="column")
        column["elements"].insert(
            0,
            {"id": "5555555", "elType": "widget", "widgetType": "crecs_property_rates",
             "settings": {}, "elements": []},
        )
        self.assertIn("E-LOADER-ORDER", codes(run(env)))

    def test_two_loaders_is_a_cardinality_error(self):
        env = minimal_envelope()
        column = find(env, el_type="column")
        column["elements"].append(
            {"id": "4444444", "elType": "widget", "widgetType": "crecs_property_data",
             "settings": {"slug": ""}, "elements": []}
        )
        self.assertIn("E-CARDINALITY", codes(run(env)))

    def test_two_maps_is_a_cardinality_error_with_the_reason(self):
        env = minimal_envelope()
        column = find(env, el_type="column")
        for eid in ("4444441", "4444442"):
            column["elements"].append(
                {"id": eid, "elType": "widget", "widgetType": "crecs_property_map",
                 "settings": {}, "elements": []}
            )
        result = run(env)
        item = [f for f in result.findings if f.code == "E-CARDINALITY"][0]
        self.assertIn("crecs_map_widget_plot_pov", item.message)

    def test_two_suites_instances_are_allowed(self):
        env = minimal_envelope()
        column = find(env, el_type="column")
        for eid, hidden in (("4444443", "hide_mobile"), ("4444444", "hide_desktop")):
            column["elements"].append(
                {"id": eid, "elType": "widget", "widgetType": "crecs_property_suites",
                 "settings": {hidden: hidden}, "elements": []}
            )
        self.assertNotIn("E-CARDINALITY", codes(run(env)))


class TestBindings(unittest.TestCase):
    def test_a_valid_binding_passes(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["__dynamic__"] = {
            "title": '[elementor-tag id="c9ca4f5" name="crecs-property" '
                     'settings="%7B%22param_name%22%3A%22property_name%22%7D"]'
        }
        self.assertNotIn("E-BINDING-CORRUPT", codes(run(env)))
        self.assertNotIn("E-BINDING-PARAM", codes(run(env)))

    def test_a_corrupted_binding_is_an_error(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["__dynamic__"] = {"title": "[elementor-tag name=crecs"}
        self.assertIn("E-BINDING-CORRUPT", codes(run(env)))

    def test_an_unknown_param_name_is_an_error(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["__dynamic__"] = {
            "title": '[elementor-tag id="c9ca4f5" name="crecs-property" '
                     'settings="%7B%22param_name%22%3A%22size-available_sf%22%7D"]'
        }
        result = run(env)
        self.assertIn("E-BINDING-PARAM", codes(result))
        item = [f for f in result.findings if f.code == "E-BINDING-PARAM"][0]
        self.assertIn("size-available_SF", item.message)

    def test_property_name_binding_is_recognised_as_present(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["__dynamic__"] = {
            "title": '[elementor-tag id="c9ca4f5" name="crecs-property" '
                     'settings="%7B%22param_name%22%3A%22property_name%22%7D"]'
        }
        result = run(env)
        self.assertIn("property_name", result.summary["bound_params"])

    def test_an_unresolved_popup_reference_is_an_unresolved_dependency(self):
        env = minimal_envelope()
        button = find(env, el_type="widget", widget_type="button")
        button["settings"]["__dynamic__"] = {
            "link": '[elementor-tag id="a231826" name="popup" '
                    'settings="%7B%22popup%22%3A%224554%22%7D"]'
        }
        self.assertIn("E-DEP-UNRESOLVED", codes(run(env)))

    def test_a_popup_declared_in_the_profile_resolves(self):
        env = minimal_envelope()
        button = find(env, el_type="widget", widget_type="button")
        button["settings"]["__dynamic__"] = {
            "link": '[elementor-tag id="a231826" name="popup" '
                    'settings="%7B%22popup%22%3A%224554%22%7D"]'
        }
        prof = Profile({"popups": {"4554": "Talk to an advisor"}})
        self.assertNotIn("E-DEP-UNRESOLVED", codes(run(env, profile=prof)))

    def test_a_missing_link_replaced_by_a_hash_is_not_accepted_as_functional(self):
        env = minimal_envelope()
        button = find(env, el_type="widget", widget_type="button")
        button["settings"]["link"] = {"url": "#", "is_external": "", "nofollow": ""}
        self.assertIn("E-DEP-PLACEHOLDER-LINK", codes(run(env)))


def _logo_tag(name="crecs-company-logo", settings="%7B%7D", instance_id="a1b2c3d"):
    """The saved form Elementor writes for a tag with no controls."""
    if settings is None:
        return '[elementor-tag id="%s" name="%s"]' % (instance_id, name)
    return '[elementor-tag id="%s" name="%s" settings="%s"]' % (instance_id, name, settings)


def _with_image_widget(env, tag=None, control="image"):
    """Add an image widget bound through `tag` on `control` to the minimal document."""
    column = env["content"][0]["elements"][0]
    column["elements"].append({
        "id": "1000009", "elType": "widget", "widgetType": "image", "isInner": False,
        "settings": {"image": {"url": "", "id": ""}, "__dynamic__": {control: tag or _logo_tag()}},
        "elements": [],
    })
    return env


class TestRegisteredTagsOtherThanProperty(unittest.TestCase):
    """The catalog's registered tags are checked, not just waved through as 'outside the
    catalog': the two logo tags (the client's company logo and flyer logo, kept in CRE
    Cloud) have no controls, take an image control, and give an empty value to a binding
    saved without a settings string. A typo in a tag's name prints nothing, silently."""

    def findings(self, env, code):
        return [f for f in run(env).findings if f.code == code]

    def new_errors(self, env):
        """The error codes this document has beyond what the plain minimal one has."""
        return sorted(set(f.code for f in run(env).findings if f.severity == "ERROR")
                      - set(f.code for f in run(minimal_envelope()).findings if f.severity == "ERROR"))

    def test_the_catalog_registers_both_logo_tags_as_image_tags_with_no_params(self):
        # What the branch below stands on: if the catalog stops saying so, the rest means
        # nothing.
        for name in ("crecs-company-logo", "crecs-flyer-logo"):
            tag = CATALOG.dynamic_tag(name)
            self.assertIsNotNone(tag, name)
            self.assertTrue(tag["registered"])
            self.assertEqual(["image"], tag["categories"])
            self.assertEqual([], tag["params"])
            self.assertIn(name, CATALOG.dynamic_tag_names())

    def test_a_logo_tag_on_an_image_control_is_checked_and_passes(self):
        for name in ("crecs-company-logo", "crecs-flyer-logo"):
            with self.subTest(tag=name):
                env = _with_image_widget(minimal_envelope(), _logo_tag(name))
                self.assertEqual([], self.new_errors(env))
                self.assertEqual([], [c for c in codes(run(env)) if "BINDING" in c and c != "W-BINDING-NON-SCALAR"])

    def test_a_typo_in_a_tags_name_is_an_error_that_names_the_real_tag(self):
        for typo in ("crecs-company-logos", "crecs-company-logo2", "crecs_company_logo", "crecs-compnay-logo",
                     "crecs-flyer-logos"):
            with self.subTest(typo=typo):
                found = self.findings(_with_image_widget(minimal_envelope(), _logo_tag(typo)), "E-BINDING-TAG")
                self.assertEqual(1, len(found), typo)
                self.assertEqual("ERROR", found[0].severity)
                self.assertIn(typo, found[0].message)
                self.assertTrue("crecs-company-logo" in found[0].message or "crecs-flyer-logo" in found[0].message,
                                "it does not say which tag was meant: " + found[0].message)
                self.assertEqual("image", found[0].control)

    def test_a_tag_of_another_plugin_is_still_only_information(self):
        # Elementor's own and other plugins' tags are outside the catalog and are kept
        # untouched: only the plugin's own names are closed.
        result = run(_with_image_widget(minimal_envelope(), _logo_tag("post-featured-image")))
        self.assertIn("I-BINDING-OTHER-TAG", codes(result))
        self.assertNotIn("E-BINDING-TAG", codes(result))

    def test_an_unknown_tag_that_was_already_in_the_page_is_kept_and_flagged_not_blocked(self):
        env = _with_image_widget(minimal_envelope(), _logo_tag("crecs-from-a-newer-plugin"))
        result = run(env, baseline_keys={"1000009::__dynamic__"})
        self.assertNotIn("E-BINDING-TAG", codes(result))
        self.assertEqual("WARNING", severity_of(result, "W-BINDING-TAG-PREEXISTING-UNKNOWN"))

    def test_an_image_tag_on_a_text_control_is_an_error_about_the_kind(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["__dynamic__"] = {"title": _logo_tag()}
        found = self.findings(env, "E-BINDING-CATEGORY")
        self.assertEqual(1, len(found), codes(run(env)))
        self.assertEqual("ERROR", found[0].severity)
        self.assertEqual("title", found[0].control)
        self.assertIn("picture", found[0].message)
        self.assertIn("text", found[0].message)

    def test_an_image_tag_on_a_link_control_is_an_error_about_the_kind(self):
        env = minimal_envelope()
        button = find(env, el_type="widget", widget_type="button")
        button["settings"]["__dynamic__"] = {"link": _logo_tag("crecs-flyer-logo")}
        self.assertEqual(1, len(self.findings(env, "E-BINDING-CATEGORY")))

    def test_the_kind_is_read_from_the_control_not_from_its_name(self):
        # The image widget's caption takes text; its picture takes an image.
        env = _with_image_widget(minimal_envelope(), _logo_tag(), control="caption")
        self.assertEqual(1, len(self.findings(env, "E-BINDING-CATEGORY")))
        ok = _with_image_widget(minimal_envelope(), _logo_tag(), control="image")
        self.assertEqual([], self.findings(ok, "E-BINDING-CATEGORY"))

    def test_a_stray_param_on_a_tag_without_params_is_an_error(self):
        # {"param_name":"property_name"}, URL-encoded
        stray = "%7B%22param_name%22%3A%22property_name%22%7D"
        found = self.findings(_with_image_widget(minimal_envelope(), _logo_tag(settings=stray)), "E-BINDING-PARAM")
        self.assertEqual(1, len(found))
        self.assertEqual("ERROR", found[0].severity)
        self.assertIn("param_name", found[0].message)
        self.assertEqual("image", found[0].control)

    def test_a_binding_saved_without_its_settings_string_is_an_error(self):
        # Elementor gives an empty value to a tag without the settings attribute, so the
        # logo would never show: the one form that reads fine and prints nothing.
        env = _with_image_widget(minimal_envelope(), _logo_tag(settings=None))
        found = self.findings(env, "E-BINDING-SETTINGS")
        self.assertEqual(1, len(found), codes(run(env)))
        self.assertEqual("ERROR", found[0].severity)
        self.assertIn("settings", found[0].message)

    def test_the_empty_object_in_any_spelling_is_accepted(self):
        for spelling in ("%7B%7D", "%7B %7D", "{}"):
            with self.subTest(settings=spelling):
                env = _with_image_widget(minimal_envelope(), _logo_tag(settings=spelling))
                self.assertEqual([], self.new_errors(env))

    def test_a_tag_on_a_control_that_takes_no_tag_is_a_warning(self):
        env = _with_image_widget(minimal_envelope(), _logo_tag(), control="image_size")
        self.assertIn("W-BINDING-TARGET", codes(run(env)))

    def test_the_forbidden_tag_is_still_refused_first(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["__dynamic__"] = {"title": _logo_tag("crecs-test")}
        self.assertIn("E-BINDING-FORBIDDEN-TAG", codes(run(env)))
        self.assertNotIn("E-BINDING-CATEGORY", codes(run(env)))

    def test_a_stored_picture_beside_the_binding_is_harmless(self):
        # The image widget keeps a static picture next to its binding (Elementor writes
        # one); the binding wins, and that is no finding.
        env = _with_image_widget(minimal_envelope())
        find(env, el_type="widget", widget_type="image")["settings"]["image"] = {
            "url": "/wp-content/plugins/elementor/assets/images/placeholder.png", "id": ""}
        self.assertEqual([], self.new_errors(env))


class TestFrozenContent(unittest.TestCase):
    def test_an_empty_loader_slug_blocks_as_an_unresolved_dependency(self):
        env = minimal_envelope()
        find(env, "crecs_property_data")["settings"]["slug"] = ""
        self.assertIn("E-DEP-UNRESOLVED", codes(run(env)))

    def test_a_slug_from_the_profile_resolves(self):
        env = minimal_envelope()
        find(env, "crecs_property_data")["settings"]["slug"] = "a-real-slug"
        prof = Profile({"preview_slug": "a-real-slug"})
        self.assertNotIn("E-DEP-UNRESOLVED", codes(run(env, profile=prof)))

    def test_a_known_example_slug_is_reported_as_frozen(self):
        env = minimal_envelope()
        find(env, "crecs_property_data")["settings"]["slug"] = (
            "hwy-380-fm-653-farmersville-tx-75442"
        )
        prof = Profile({"example_slugs": ["hwy-380-fm-653-farmersville-tx-75442"]})
        self.assertIn("E-FROZEN-SLUG", codes(run(env, profile=prof)))

    def test_a_forbidden_literal_in_a_setting_is_reported(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["title"] = "Farmersville 380 Business Park"
        prof = Profile({"forbidden_literals": ["Farmersville 380 Business Park"]})
        self.assertIn("E-FROZEN-CONTENT", codes(run(env, profile=prof)))

    def test_the_elementor_placeholder_title_is_not_frozen_content(self):
        env = minimal_envelope()
        heading = find(env, el_type="widget", widget_type="heading")
        heading["settings"]["title"] = "Add Your Heading Text Here"
        self.assertNotIn("E-FROZEN-CONTENT", codes(run(env)))


class TestSecretsAndAssets(unittest.TestCase):
    def test_an_api_key_looking_value_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_color"] = (
            "AIzaSyD-ExampleLookingGoogleApiKey1234567"
        )
        self.assertIn("E-SECRET", codes(run(env)))

    def test_a_bearer_token_is_an_error(self):
        env = minimal_envelope()
        env["title"] = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"
        self.assertIn("E-SECRET", codes(run(env)))

    def test_a_foreign_host_asset_is_a_warning_and_an_unresolved_dependency(self):
        env = minimal_envelope()
        find(env, el_type="section")["settings"]["background_image"] = {
            "id": "5850", "url": "https://knakedodge.com/wp-content/uploads/x.png"
        }
        result = run(env)
        self.assertIn("W-CROSS-SITE-ASSET", codes(result))
        self.assertIn("E-DEP-UNRESOLVED", codes(result))

    def test_a_host_declared_in_the_profile_is_accepted(self):
        env = minimal_envelope()
        find(env, el_type="section")["settings"]["background_image"] = {
            "id": "5850", "url": "https://client.example/wp-content/uploads/x.png"
        }
        prof = Profile({"site_host": "client.example", "media": {"5850": "ok"}})
        self.assertNotIn("E-DEP-UNRESOLVED", codes(run(env, profile=prof)))


class TestPreferencesAreNotRestrictions(unittest.TestCase):
    def test_literal_colour_is_info_only(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_color"] = "#111D28"
        result = run(env)
        self.assertEqual(severity_of(result, "I-LITERAL-COLOR"), "INFO")
        self.assertNotIn("E-CONTROL-TYPE", codes(result))

    def test_a_14px_font_size_is_not_flagged_as_a_restriction(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"][
            "field_label_typography_font_size"
        ] = {"unit": "px", "size": 14, "sizes": []}
        result = run(env)
        self.assertEqual([f for f in result.findings
                          if f.severity == "ERROR" and "font_size" in f.message], [])


class TestRepeaters(unittest.TestCase):
    def test_a_repeater_row_without_an_id_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["pa_condition_repeater"] = [
            {"pa_condition_key": "x"}
        ]
        baseline = {find(env, "crecs_property_fields")["id"] + "::pa_condition_repeater"}
        self.assertIn("E-REPEATER-SHAPE", codes(run(env, baseline_keys=baseline)))

    def test_an_empty_repeater_is_valid_and_distinct_from_absent(self):
        env = minimal_envelope()
        widget = find(env, "crecs_property_fields")
        widget["settings"]["pa_condition_repeater"] = []
        baseline = {widget["id"] + "::pa_condition_repeater"}
        self.assertNotIn("E-REPEATER-SHAPE", codes(run(env, baseline_keys=baseline)))


class TestCoverageAndRemoval(unittest.TestCase):
    def test_a_missing_relevant_widget_is_a_warning(self):
        result = run(minimal_envelope())
        self.assertEqual(severity_of(result, "W-COVERAGE"), "WARNING")

    def test_removing_a_required_widget_without_a_reason_is_flagged(self):
        env = minimal_envelope()
        column = find(env, el_type="column")
        column["elements"] = [
            e for e in column["elements"] if e.get("widgetType") != "crecs_property_data"
        ]
        result = run(env)
        self.assertIn("E-LOADER-MISSING", codes(result))
        item = [f for f in result.findings if f.code == "E-LOADER-MISSING"][0]
        self.assertIn("session", item.message.lower())

    def test_unknown_widget_type_is_preserved_and_flagged(self):
        env = minimal_envelope()
        column = find(env, el_type="column")
        column["elements"].append(
            {"id": "3333331", "elType": "widget", "widgetType": "some_other_addon",
             "settings": {"foo": 1}, "elements": []}
        )
        result = run(env)
        self.assertEqual(severity_of(result, "W-WIDGET-UNKNOWN"), "WARNING")
        self.assertNotIn("E-CONTROL-UNKNOWN", codes(result))


class TestResultShape(unittest.TestCase):
    def test_findings_carry_a_path_and_an_element_id(self):
        env = minimal_envelope()
        find(env, "crecs_property_fields")["settings"]["card_glow_intensity"] = 1
        item = [f for f in run(env).findings if f.code == "E-CONTROL-UNKNOWN"][0]
        self.assertTrue(item.element_id)
        self.assertTrue(item.path)

    def test_counts_are_reported_by_severity(self):
        result = run(minimal_envelope())
        for key in ("ERROR", "WARNING", "INFO"):
            self.assertIn(key, result.counts)

    def test_is_exportable_reflects_errors_only(self):
        clean = run(minimal_envelope())
        self.assertEqual(clean.counts["ERROR"] == 0, clean.is_exportable)


if __name__ == "__main__":
    unittest.main()


class TestNumericAgainstStringOptions(unittest.TestCase):
    """Elementor compares option values as strings, so a number where the vocabulary
    is strings silently fails to match. That has to be caught, not coerced."""

    def test_a_number_against_a_string_vocabulary_is_an_error(self):
        env = minimal_envelope()
        find(env, "crecs_property_suites")["settings"] = {
            "card_header_typography_font_weight": 700
        }
        result = run(env)
        self.assertIn("E-CONTROL-TYPE", codes(result))
        item = [f for f in result.findings if f.code == "E-CONTROL-TYPE"][0]
        self.assertIn("'700'", item.hint)

    def test_the_string_form_passes(self):
        env = minimal_envelope()
        find(env, "crecs_property_suites")["settings"] = {
            "card_header_typography_font_weight": "700"
        }
        self.assertNotIn("E-CONTROL-TYPE", codes(run(env)))
