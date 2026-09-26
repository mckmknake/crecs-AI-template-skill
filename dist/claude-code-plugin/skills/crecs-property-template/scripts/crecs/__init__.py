"""crecs-property-template — offline tooling for the shared CRECS Elementor
property template.

Python 3.9+, standard library only. No network access, no WordPress, no PHP, no
CRE Cloud credentials. Everything it knows about the widgets comes from the
generated projection in ../references/catalog/.
"""

__version__ = "1.1.0"

# The delivery-1 catalog this package was generated against. `selftest` checks that
# the shipped projection still reports the same provenance.
EXPECTED_PLUGIN_REVISION = "b3844c40bc4131c6a30db402a378a151348d6b40"
