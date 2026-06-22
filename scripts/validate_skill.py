#!/usr/bin/env python3
"""SKILL.md の frontmatter 検証"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed", file=sys.stderr)
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"

REQUIRED_FIELDS = ["name", "description"]
MAX_DESCRIPTION_LENGTH = 1024


def main():
    if not SKILL_MD.exists():
        print(f"ERROR: {SKILL_MD} not found", file=sys.stderr)
        sys.exit(1)

    content = SKILL_MD.read_text(encoding="utf-8")
    if not content.startswith("---"):
        print("ERROR: SKILL.md must start with YAML frontmatter (---)", file=sys.stderr)
        sys.exit(1)

    parts = content.split("---", 2)
    if len(parts) < 3:
        print("ERROR: SKILL.md frontmatter is malformed", file=sys.stderr)
        sys.exit(1)

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as e:
        print(f"ERROR: YAML parse error in frontmatter: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(frontmatter, dict):
        print("ERROR: frontmatter must be a dict", file=sys.stderr)
        sys.exit(1)

    errors = []
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    desc = frontmatter.get("description", "")
    if len(desc) > MAX_DESCRIPTION_LENGTH:
        errors.append(f"description too long: {len(desc)} chars (max {MAX_DESCRIPTION_LENGTH})")

    name = frontmatter.get("name", "")
    if name and not name.replace("-", "").replace("_", "").isalnum():
        errors.append(f"name must be alphanumeric with - or _: {name}")

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ SKILL.md validated. name={name}, description={len(desc)} chars")


if __name__ == "__main__":
    main()
