#!/usr/bin/env python3

import sys

_MIN_PYTHON_VER = (3, 6)
if sys.version_info < _MIN_PYTHON_VER:
    sys.exit("[wavcheck] ERROR: Requires Python %s.%s or newer" % _MIN_PYTHON_VER)


from .main import cli

if __name__ == "__main__":
    cli()
