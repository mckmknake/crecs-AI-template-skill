"""Contract for the export envelope and the export gate."""

import copy
import unittest

from crecs.document import Document
from crecs import export as export_mod

from tests.helpers import minimal_envelope


class TestEnvelope(unittest.TestCase):
    def test_exactly_the_five_elementor_keys_in_order(self):
        envelope = export_mod.build_envelope(Document(minimal_envelope()))
        self.assertEqual(list(envelope.keys()),
                         ["content", "page_settings", "version", "title", "type"])

    def test_bookkeeping_keys_are_dropped(self):
        payload = minimal_envelope()
        payload["crecs_studio_revision"] = 7
        payload["notes"] = "internal"
        envelope = export_mod.build_envelope(Document(payload))
        self.assertNotIn("crecs_studio_revision", envelope)
        self.assertNotIn("notes", envelope)

    def test_a_bare_array_gains_a_default_envelope(self):
        document = Document(copy.deepcopy(minimal_envelope()["content"]))
        envelope = export_mod.build_envelope(document, title="Given title")
        self.assertEqual(envelope["version"], "0.4")
        self.assertEqual(envelope["type"], "page")
        self.assertEqual(envelope["title"], "Given title")

    def test_the_content_tree_is_untouched(self):
        payload = minimal_envelope()
        before = copy.deepcopy(payload["content"])
        envelope = export_mod.build_envelope(Document(payload))
        self.assertEqual(envelope["content"], before)

    def test_page_settings_is_preserved_when_present(self):
        payload = minimal_envelope()
        payload["page_settings"] = {"background_background": "classic"}
        envelope = export_mod.build_envelope(Document(payload))
        self.assertEqual(envelope["page_settings"],
                         {"background_background": "classic"})

    def test_internal_prefixed_element_keys_are_stripped(self):
        payload = minimal_envelope()
        payload["content"][0]["settings"]["_crecs_scratch"] = "remove me"
        envelope = export_mod.build_envelope(Document(payload))
        removed = export_mod._strip_internal(envelope)
        self.assertIn("_crecs_scratch", removed)
        self.assertNotIn("_crecs_scratch", envelope["content"][0]["settings"])

    def test_ordinary_underscore_keys_are_kept(self):
        payload = minimal_envelope()
        payload["content"][0]["settings"]["_title"] = "Property Data"
        envelope = export_mod.build_envelope(Document(payload))
        export_mod._strip_internal(envelope)
        self.assertEqual(envelope["content"][0]["settings"]["_title"], "Property Data")


if __name__ == "__main__":
    unittest.main()
