"""The catalog references the skill ships name no site.

Everything under references/ is generated from a dump of one WordPress install, in
practice the developer's own Local site. Elementor computes some control defaults from
that install's address: the image widget's placeholder is
ELEMENTOR_ASSETS_URL . 'images/placeholder.png'. So until 2026-09-28 the projection
shipped the developer's hostname to every client, inside a URL that points at a machine
no client can reach. (This file ships in every package too, which is why it does not
name that host.)

The projection builder in the plugin repository
(tools/crecs-template-studio/build-references.js) now records such defaults site-relative
and refuses to write an absolute address. These cases hold the shipped files to that.
The first proves the detector can see the defect, so a broken detector fails instead of
passing forever.
"""

import copy
import json
import os
import re
import unittest

from crecs.catalog import Catalog

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(os.path.dirname(HERE))
REFERENCES = os.path.join(SKILL_ROOT, "references")
PROJECTION = os.path.join(REFERENCES, "catalog", "crecs-controls.min.json")

# Any absolute web address. The references describe controls, not sites, so none
# belongs in them: a default Elementor derives from the site's address is recorded as a
# path, and the target site supplies its own origin.
ABSOLUTE_URL = re.compile(r"https?://[^\s\"'`)<>|]+", re.IGNORECASE)

PLACEHOLDER_PATH = "/wp-content/plugins/elementor/assets/images/placeholder.png"

REGENERATE = ("Regenerate references/ with the plugin repository's "
              "tools/crecs-template-studio/build-references.js, which records "
              "site-derived defaults site-relative.")


def absolute_urls(text):
    return ABSOLUTE_URL.findall(text)


def reference_files():
    for dirpath, _dirs, names in os.walk(REFERENCES):
        for name in sorted(names):
            if name.endswith((".json", ".md")):
                yield os.path.join(dirpath, name)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


class ReferencesNameNoSite(unittest.TestCase):

    def test_the_detector_sees_a_site_address(self):
        # Break a copy: put a development host back into the image default the way
        # the extractor records it, then require the detector to report exactly that.
        broken = copy.deepcopy(json.loads(read(PROJECTION)))
        leaked = "http://dev-site.test" + PLACEHOLDER_PATH
        broken["core_widgets"]["image"]["controls"]["image"]["default"]["url"] = leaked
        self.assertEqual([leaked], absolute_urls(json.dumps(broken)))

    def test_no_reference_file_names_a_site(self):
        hits = {}
        for path in reference_files():
            found = absolute_urls(read(path))
            if found:
                hits[os.path.relpath(path, SKILL_ROOT).replace(os.sep, "/")] = found
        self.assertEqual({}, hits, "the shipped references name a site. " + REGENERATE)

    def test_the_image_placeholder_default_is_site_relative(self):
        control = Catalog.load_default().control("image", "image")
        self.assertIsNotNone(control, "the core image widget lost its image control")
        default = control.data.get("default") or {}
        self.assertEqual(PLACEHOLDER_PATH, default.get("url"), REGENERATE)
        self.assertIs(True, control.data.get("default_site_relative"),
                      "the projection must mark a site-relative default, so the "
                      "reference page can say what it means. " + REGENERATE)


if __name__ == "__main__":
    unittest.main()
