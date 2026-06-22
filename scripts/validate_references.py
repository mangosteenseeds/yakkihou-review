#!/usr/bin/env python3
"""references/ ディレクトリの整合性チェック"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = REPO_ROOT / "references"

REQUIRED_FILES = [
    "efficacy-56.md",
    "ng-expressions.md",
    "keihyouhou.md",
    "before-after-testimonials.md",
]


def main():
    errors = []

    if not REFERENCES_DIR.exists():
        print(f"ERROR: {REFERENCES_DIR} not found", file=sys.stderr)
        sys.exit(1)

    for required in REQUIRED_FILES:
        path = REFERENCES_DIR / required
        if not path.exists():
            errors.append(f"Missing required reference file: {required}")
            continue
        content = path.read_text(encoding="utf-8")
        if len(content) < 100:
            errors.append(f"Reference file too short (suspicious): {required} ({len(content)} chars)")
        if not content.startswith("#"):
            errors.append(f"Reference file should start with H1 heading: {required}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ All {len(REQUIRED_FILES)} required reference files validated.")


if __name__ == "__main__":
    main()
