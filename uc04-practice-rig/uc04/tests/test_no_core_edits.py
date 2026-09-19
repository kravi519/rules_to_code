"""tests/test_no_core_edits.py — PRE-BUILT. Checks against a manifest built by
tools/manifest.py at "kick-off" (i.e. now, for this practice rig). Run
`python3 tools/manifest.py write` once at the start of a session, then this
test (and `make verify`) will catch any edit outside ai/.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.manifest import check


def test_no_core_edits():
    ok, changed = check()
    assert ok, f"files changed outside ai/: {changed}"
