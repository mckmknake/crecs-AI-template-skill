"""The canonical hash is a contract between two implementations, in two languages.

`crecs_preview.py` computes it in Python and the preview module computes it in PHP, and
they must agree byte for byte: the hash is what lets the export claim "this file is the
thing you saw rendered". If they disagree the claim is void, and the only symptom is a
warning nobody reads.

They did disagree. `canonical()` ends in `json_encode()`, whose float formatting follows
PHP's `serialize_precision`. This site's CLI had `-1`, its web process had `17`, so the
same document hashed one way from the command line and another way through REST —
`1.15` against `1.1499999999999999`. Two servers with different php.ini would have
disagreed the same way.

EXPECTED below is the agreement. `tools/preview-tests/run.php` asserts the same literal
in case F1-03. If one side changes, both fail.
"""

import hashlib
import json
import unittest

from crecs_preview import canonical_hash

# Floats chosen to break naive formatting: 1.15 and 2.675 are the classic cases where
# the shortest round-trip form and a fixed-precision expansion differ. The slash in the
# URL guards the other half of the rule — slashes stay unescaped.
DOC = json.loads(
    '[{"id":"aaa1","elType":"section","isInner":false,"settings":'
    '{"_title":"Floats","line_height":{"unit":"em","size":1.15,"sizes":[]},'
    '"zoom":{"unit":"px","size":0.1,"sizes":[]},"ratio":2.675,"whole":3,'
    '"url":"https://example.test/a/b.png"},"elements":[]}]'
)

EXPECTED = "063d9ab4d83d2e86bae08d07b15cbe742bd0ecef3d13f4770a7396ab7fd77ec4"

CANONICAL = (
    '[{"elType":"section","elements":[],"id":"aaa1","isInner":false,'
    '"settings":{"_title":"Floats","line_height":{"size":1.15,"sizes":[],"unit":"em"},'
    '"ratio":2.675,"url":"https://example.test/a/b.png","whole":3,'
    '"zoom":{"size":0.1,"sizes":[],"unit":"px"}}}]'
)


class CanonicalHash(unittest.TestCase):
    def test_the_pinned_hash(self):
        self.assertEqual(EXPECTED, canonical_hash(DOC))

    def test_the_canonical_string_is_what_we_think_it_is(self):
        # Pinning the string as well as the hash means a failure says WHICH rule broke,
        # not just that two hex strings differ.
        self.assertEqual(EXPECTED, hashlib.sha256(CANONICAL.encode("utf-8")).hexdigest())

    def test_floats_use_their_shortest_round_trip_form(self):
        self.assertIn('"size":1.15', CANONICAL)
        self.assertNotIn("1.1499999999999999", CANONICAL)
        self.assertIn('"ratio":2.675', CANONICAL)

    def test_a_whole_number_stays_an_integer(self):
        # 3 must not become 3.0: PHP would write 3 and Python must too.
        self.assertIn('"whole":3', CANONICAL)
        self.assertNotIn('"whole":3.0', CANONICAL)

    def test_slashes_are_not_escaped(self):
        self.assertIn("https://example.test/a/b.png", CANONICAL)
        self.assertNotIn("\\/", CANONICAL)

    def test_keys_are_sorted_recursively(self):
        self.assertLess(CANONICAL.index('"elType"'), CANONICAL.index('"id"'))
        self.assertLess(CANONICAL.index('"size"'), CANONICAL.index('"unit"'))

    def test_key_order_in_the_input_does_not_matter(self):
        shuffled = json.loads(json.dumps(DOC))
        shuffled[0]["settings"] = dict(reversed(list(shuffled[0]["settings"].items())))
        self.assertEqual(canonical_hash(DOC), canonical_hash(shuffled))

    def test_no_whitespace_between_tokens(self):
        self.assertNotIn(", ", CANONICAL)
        self.assertNotIn(": ", CANONICAL)


if __name__ == "__main__":
    unittest.main()
