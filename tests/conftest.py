"""Pytest bootstrap: mirror mesh-master.py's sys.path setup.

mesh-master.py inserts scripts/utilities at import time so that modules like
mesh_master_mail resolve as top-level imports. Without the same entry here,
tests that import mesh_master.* fail at collection with ModuleNotFoundError.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_UTILITIES = os.path.join(_ROOT, "scripts", "utilities")

for _p in (_UTILITIES, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
