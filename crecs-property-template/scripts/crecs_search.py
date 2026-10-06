#!/usr/bin/env python3
"""Edit the CRECS property search page's layout document. See crecs/search_cli.py."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crecs.search_cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
