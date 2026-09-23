#!/usr/bin/env python3
"""Offline test runner for the crecs-property-template package.

Runs every suite with the standard library only and then prints a coverage report
naming which widgets and which control families were exercised — and, more
importantly, which were not.

    python3 scripts/tests/run_tests.py            # everything
    python3 scripts/tests/run_tests.py --unit     # skip the conversational suite
    python3 scripts/tests/run_tests.py --json     # machine-readable summary
"""

import argparse
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from crecs.catalog import Catalog  # noqa: E402  (after sys.path setup)
from crecs import coverage  # noqa: E402


UNIT = ["tests.test_bindings", "tests.test_document", "tests.test_state",
        "tests.test_canonical_hash",
        "tests.test_validate", "tests.test_export"]
INTEGRATION = ["tests.test_cli", "tests.test_popup", "tests.test_delivery",
               "tests.test_transport_errors",
               "tests.test_bind_list", "tests.test_start_from_site"]
DOCS = ["tests.test_plain_language", "tests.test_opening_sequence"]
CONVERSATIONAL = ["tests.test_conversational"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--unit", action="store_true",
                        help="run only the unit suites")
    parser.add_argument("--conversational", action="store_true",
                        help="run only the twelve conversational scenarios")
    parser.add_argument("--json", action="store_true",
                        help="print a machine-readable summary instead of text")
    parser.add_argument("--quiet", action="store_true", help="less verbose output")
    parser.add_argument("--no-coverage", action="store_true",
                        help="skip the widget/control coverage report")
    args = parser.parse_args(argv)

    if args.unit:
        modules = UNIT
    elif args.conversational:
        modules = CONVERSATIONAL
    else:
        modules = UNIT + INTEGRATION + DOCS + CONVERSATIONAL

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for name in modules:
        suite.addTests(loader.loadTestsFromName(name))

    stream = open(os.devnull, "w") if args.json else sys.stdout
    runner = unittest.TextTestRunner(stream=stream, verbosity=1 if args.quiet else 2)
    result = runner.run(suite)
    if args.json:
        stream.close()

    report = {
        "modules": modules,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "passed": result.wasSuccessful(),
    }

    if not args.no_coverage:
        report["coverage"] = coverage.report(Catalog.load_default())

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print()
        print("tests_run=%d failures=%d errors=%d -> %s"
              % (result.testsRun, len(result.failures), len(result.errors),
                 "PASS" if result.wasSuccessful() else "FAIL"))
        if "coverage" in report:
            cov = report["coverage"]
            print()
            print("widget coverage: %d/%d relevant widgets appear in the base template "
                  "or a fixture" % (cov["widgets_covered"], cov["widgets_relevant"]))
            if cov["widgets_uncovered"]:
                print("  NOT covered: " + ", ".join(cov["widgets_uncovered"]))
            print("control families exercised by the suites: %d/%d"
                  % (cov["families_exercised"], cov["families_total"]))
            if cov["families_not_exercised"]:
                print("  NOT exercised: " + ", ".join(cov["families_not_exercised"]))
            print()
            print("Claim level: these results mean 'tested in the harness'. "
                  "No template was imported into Elementor and nothing was rendered.")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
