#!/usr/bin/env python3
"""
apply_proposals.py

update_references.py が生成した proposals.json を読み込み、
references/*.md および case-studies.md に反映する。

- new_ng_patterns → references/ng-expressions.md の該当カテゴリ末尾に追記
- regulation_updates → references/*.md の該当箇所に追記 + PR本文で詳細を要求
- case_studies → references/case-studies.md に追記(なければ作成)

PR本文を pr_body.md として書き出す。
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = REPO_ROOT / "references"


CATEGORY_HEADER_MAP = {
    "A": "## カテゴリA: 医薬品的効能",
    "B": "## カテゴリB: 身体構造・機能の変化を暗示",
    "C": "## カテゴリC: 絶対的効果保証",
    "D": "## カテゴリD: 最大級表現・序列訴求",
    "E": "## カテゴリE: 安全性の絶対断定",
    "F": "## カテゴリF: 比較広告・誹謗",
    "G": "## カテゴリG: 医療・施術と紐づける表現",
    "H": "## カテゴリH: 体験談・口コミの取扱い",
    "I": "## カテゴリI: 化粧品×食品的訴求",
    "J": "## カテゴリJ: グレーゾーン",
    "K": "## カテゴリK: ステマ規制関連",
}


def append_ng_patterns(ng_file: Path, patterns: list[dict]) -> int:
    """ng-expressions.md の末尾に追記用セクションを足す"""
    if not patterns:
        return 0

    today = datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        "",
        f"## 🆕 自動追加 ({today})",
        "",
        "_以下は月次自動更新で追加された候補です。人間レビューを経て、適切なカテゴリへ移設してください。_",
        "",
        "| 該当表現 | カテゴリ | 問題点 | 法的根拠 | 修正案 | 出典 |",
        "|---------|---------|--------|---------|--------|------|",
    ]
    for p in patterns:
        url = p.get("source_url", "")
        title = p.get("source_title", "出典")
        source_link = f"[{title}]({url})" if url else title
        row = "| {expr} | {cat} | {problem} | {legal} | {rewrite} | {src} |".format(
            expr=escape_pipe(p.get("expression", "")),
            cat=p.get("category", "J"),
            problem=escape_pipe(p.get("problem", "")),
            legal=escape_pipe(p.get("legal_basis", "")),
            rewrite=escape_pipe(p.get("rewrite_suggestion", "")),
            src=escape_pipe(source_link),
        )
        lines.append(row)
    lines.append("")

    with ng_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return len(patterns)


def append_case_studies(case_file: Path, cases: list[dict]) -> int:
    """case-studies.md に追記(なければ新規作成)"""
    if not cases:
        return 0

    today = datetime.utcnow().strftime("%Y-%m-%d")

    if not case_file.exists():
        case_file.write_text(
            "# 措置命令・行政指導事例集\n\n"
            "化粧品・美容関連の景表法措置命令、薬機法行政指導の事例を蓄積する。\n"
            "**出典は必ず明示すること**。事業者名は公表情報のみ記載。\n\n",
            encoding="utf-8",
        )

    lines = [
        "",
        f"## 🆕 自動追加 ({today})",
        "",
    ]
    for c in cases:
        violated_exprs = c.get("violated_expressions", [])
        violated_laws = c.get("violated_laws", [])
        lines.extend([
            f"### {c.get('case_name', 'Unknown')} ({c.get('date', 'date unknown')})",
            "",
            f"- **所管**: {c.get('agency', '不明')}",
            f"- **違反法令**: {', '.join(violated_laws) if violated_laws else '不明'}",
            f"- **概要**: {c.get('summary', '')}",
            "- **違反とされた表現**:",
        ])
        for expr in violated_exprs:
            lines.append(f"  - 「{expr}」")
        url = c.get("source_url", "")
        if url:
            lines.append(f"- **出典**: {url}")
        lines.append("")

    with case_file.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return len(cases)


def write_regulation_update_marker(reg_updates: list[dict]) -> str:
    """references/REGULATION-UPDATES-PENDING.md にpending状態として記録"""
    if not reg_updates:
        return ""

    pending_file = REFERENCES_DIR / "REGULATION-UPDATES-PENDING.md"
    today = datetime.utcnow().strftime("%Y-%m-%d")

    lines = [
        f"# Pending Regulation Updates",
        "",
        "**This file lists regulation/guideline updates that require human review and manual integration into the appropriate reference files.**",
        "",
        "Once integrated, remove the entry from this file.",
        "",
        f"## Detected on {today}",
        "",
    ]
    for r in reg_updates:
        affected = r.get("affected_files", [])
        lines.extend([
            f"### {r.get('law', 'Unknown law')}",
            "",
            f"- **Effective Date**: {r.get('effective_date', 'TBD')}",
            f"- **Summary**: {r.get('summary', '')}",
            f"- **Affected Files**: {', '.join(affected) if affected else '(to be determined)'}",
            f"- **Proposed Changes**: {r.get('proposed_changes', '')}",
            f"- **Source**: {r.get('source_url', '')}",
            "",
            "---",
            "",
        ])

    # 既存があれば追記、なければ新規
    if pending_file.exists():
        existing = pending_file.read_text(encoding="utf-8")
        # 先頭ヘッダは1度だけにしたい
        pending_file.write_text(existing + "\n\n" + "\n".join(lines[4:]), encoding="utf-8")
    else:
        pending_file.write_text("\n".join(lines), encoding="utf-8")

    return str(pending_file.relative_to(REPO_ROOT))


def escape_pipe(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def build_pr_body(proposals: dict) -> str:
    summary = proposals.get("summary", "")
    ng_count = len(proposals.get("new_ng_patterns", []))
    reg_count = len(proposals.get("regulation_updates", []))
    case_count = len(proposals.get("case_studies", []))
    lookback = proposals.get("lookback_days", "?")

    lines = [
        "## 🤖 Automated Monthly References Update",
        "",
        f"**Generated at**: `{proposals.get('generated_at', '')}`  ",
        f"**Lookback window**: {lookback} days  ",
        f"**Total proposals**: {ng_count + reg_count + case_count}",
        "",
        "### Summary",
        summary or "_(no summary provided)_",
        "",
        "### Counts",
        f"- 🆕 New NG patterns: **{ng_count}**",
        f"- 📜 Regulation updates: **{reg_count}**",
        f"- ⚖️ Case studies: **{case_count}**",
        "",
        "---",
        "",
        "## ⚠️ Human Review Required",
        "",
        "This PR was generated by `update_references.py` via the Anthropic API with web search.",
        "**All proposals must be reviewed by a human maintainer before merging.**",
        "",
        "### Review checklist",
        "- [ ] 各提案の出典URLを実際に開き、内容を確認した",
        "- [ ] 既存 references との重複・矛盾がないか確認した",
        "- [ ] 新規NGパターンは適切なカテゴリ(A〜K)に分類されている",
        "- [ ] case-studies.md の事業者名は公表情報のみであり、推定情報を含まない",
        "- [ ] 法令改正の発効日が正確である",
        "- [ ] 修正案(rewrite_suggestion)が56効能の範囲内である",
        "- [ ] 微妙な解釈が必要な箇所は専門家(薬事行政書士/弁護士)確認を経た",
        "",
        "### Quick reference",
        "",
    ]

    if ng_count > 0:
        lines.append("#### New NG patterns (preview)")
        for p in proposals["new_ng_patterns"][:5]:
            lines.append(f"- **{p.get('expression', '')}** (cat {p.get('category', '?')}): {p.get('problem', '')[:100]}")
        if ng_count > 5:
            lines.append(f"- ...and {ng_count - 5} more")
        lines.append("")

    if reg_count > 0:
        lines.append("#### Regulation updates (preview)")
        for r in proposals["regulation_updates"][:5]:
            lines.append(f"- **{r.get('law', '')}** (eff. {r.get('effective_date', 'TBD')}): {r.get('summary', '')[:100]}")
        lines.append("")
        lines.append("> ⚠️ Regulation updates are written to `references/REGULATION-UPDATES-PENDING.md` for manual integration.")
        lines.append("")

    if case_count > 0:
        lines.append("#### Case studies (preview)")
        for c in proposals["case_studies"][:5]:
            lines.append(f"- **{c.get('case_name', '')}** ({c.get('date', '')}): {c.get('summary', '')[:120]}")
        if case_count > 5:
            lines.append(f"- ...and {case_count - 5} more")
        lines.append("")

    lines.extend([
        "---",
        "",
        "_Generated by [.github/workflows/monthly-update.yml](.github/workflows/monthly-update.yml)_",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--pr-body-out", default="pr_body.md")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    proposals = json.loads(input_path.read_text(encoding="utf-8"))

    ng_count = append_ng_patterns(
        REFERENCES_DIR / "ng-expressions.md",
        proposals.get("new_ng_patterns", []),
    )

    case_count = append_case_studies(
        REFERENCES_DIR / "case-studies.md",
        proposals.get("case_studies", []),
    )

    pending_file = write_regulation_update_marker(proposals.get("regulation_updates", []))

    print(f"[apply_proposals] Applied: ng={ng_count}, cases={case_count}")
    if pending_file:
        print(f"[apply_proposals] Regulation updates written to: {pending_file}")

    pr_body = build_pr_body(proposals)
    Path(args.pr_body_out).write_text(pr_body, encoding="utf-8")
    print(f"[apply_proposals] PR body written to: {args.pr_body_out}")


if __name__ == "__main__":
    main()
