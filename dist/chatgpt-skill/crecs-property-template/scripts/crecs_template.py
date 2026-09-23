#!/usr/bin/env python3
"""crecs-property-template — command line entry point.

    python3 crecs_template.py --help

Offline, Python 3.9+, standard library only. No WordPress, no PHP, no network, no
CRE Cloud credentials.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crecs.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
