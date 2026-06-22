#!/usr/bin/env python3
"""
update_changelog.py

CHANGELOG.md の [Unreleased] セクションに、proposals.json の内容を追記する。
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--proposals", required=True)
    args = parser.parse_args()

    data = json.loads(Path(args.proposals).read_text(encoding="utf-8"))
    today = datetime.utcnow().strftime("%Y-%m-%d")

    ng_count = len(data.get("new_ng_patterns", []))
    reg_count = len(data.get("regulation_updates", []))
    case_count = len(data.get("case_studies", []))

    if (ng_count + reg_count + case_count) == 0:
        print("[update_changelog] No changes to record.")
        return

    entry_lines = [
        f"### Added ({today} - automated)",
    ]
    if ng_count:
        entry_lines.append(f"- {ng_count} new NG expression(s) appended to `references/ng-expressions.md`")
    if case_count:
        entry_lines.append(f"- {case_count} case study/studies appended to `references/case-studies.md`")
    if reg_count:
        entry_lines.append(f"- {reg_count} pending regulation update(s) in `references/REGULATION-UPDATES-PENDING.md`")
    entry_lines.append("")

    entry = "\n".join(entry_lines)

    content = CHANGELOG.read_text(encoding="utf-8")
    if "## [Unreleased]" in content:
        # [Unreleased] の直下に挿入
        before, after = content.split("## [Unreleased]", 1)
        # afterの先頭から次の "## [" までの間に追加
        next_heading_idx = after.find("\n## [")
        if next_heading_idx == -1:
            new_content = before + "## [Unreleased]\n\n" + entry + "\n" + after.lstrip()
        else:
            unreleased_body = after[:next_heading_idx]
            rest = after[next_heading_idx:]
            new_content = (
                before
                + "## [Unreleased]\n\n"
                + entry + "\n"
                + unreleased_body.lstrip().lstrip("\n")
                + rest
            )
        CHANGELOG.write_text(new_content, encoding="utf-8")
    else:
        # [Unreleased] セクションがない場合は先頭付近に追加
        CHANGELOG.write_text(
            content + f"\n## [Unreleased]\n\n{entry}\n",
            encoding="utf-8",
        )

    print(f"[update_changelog] Updated CHANGELOG.md with {ng_count + reg_count + case_count} entries.")


if __name__ == "__main__":
    main()
