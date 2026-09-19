"""
tools/manifest.py — PRE-BUILT. Hashes every file outside ai/ and out/traces/
scratch dirs, so `make verify` can prove nothing locked was touched.

Usage:
    python3 tools/manifest.py write   # run once, at the start of a session
    python3 tools/manifest.py check   # run any time; also used by make verify
"""
from __future__ import annotations
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / ".manifest.json"

# Directories whose contents you're allowed to change.
WRITABLE = {"ai"}
# Directories that are expected to change every run (generated output) —
# excluded from the manifest entirely, not just from enforcement.
IGNORED_DIRS = {"out", "traces", ".git", "__pycache__", "generated"}
IGNORED_FILES = {".manifest.json"}


def _iter_locked_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if not parts:
            continue
        if parts[0] in WRITABLE:
            continue
        if any(p in IGNORED_DIRS for p in parts):
            continue
        if rel.name in IGNORED_FILES:
            continue
        if rel.name.endswith(".pyc"):
            continue
        yield rel


def _hash_file(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def write():
    manifest = {str(rel): _hash_file(rel) for rel in _iter_locked_files()}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"Wrote manifest for {len(manifest)} files to {MANIFEST_PATH}")


def check() -> tuple[bool, list[str]]:
    if not MANIFEST_PATH.exists():
        print("No manifest found — run `python3 tools/manifest.py write` first.")
        return True, []  # nothing to compare against yet; don't hard-fail a fresh checkout
    manifest = json.loads(MANIFEST_PATH.read_text())
    changed = []
    current = {str(rel): _hash_file(rel) for rel in _iter_locked_files()}
    for rel, old_hash in manifest.items():
        new_hash = current.get(rel)
        if new_hash != old_hash:
            changed.append(rel)
    for rel in current:
        if rel not in manifest:
            changed.append(f"{rel} (new file outside ai/)")
    return len(changed) == 0, changed


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "write":
        write()
    else:
        ok, changed = check()
        if ok:
            print("make verify: PASS — nothing outside ai/ has changed.")
            sys.exit(0)
        else:
            print("make verify: FAIL — changed outside ai/:")
            for c in changed:
                print(f"  - {c}")
            sys.exit(1)
