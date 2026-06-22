#!/usr/bin/env python3
"""
update_references.py

Claude API + web_search を使って、先月以降の景品表示法措置命令・薬機法関連通知を調査し、
references/ に追加すべき更新提案を構造化JSON として出力する。

出力JSONスキーマ:
{
  "generated_at": "ISO8601",
  "lookback_days": 31,
  "new_ng_patterns": [
    {
      "expression": "string",
      "category": "A|B|C|D|E|F|G|H|I|J|K",
      "problem": "string",
      "legal_basis": "string",
      "rewrite_suggestion": "string",
      "source_url": "string",
      "source_title": "string",
      "source_date": "YYYY-MM-DD"
    }
  ],
  "regulation_updates": [
    {
      "law": "string",
      "summary": "string",
      "effective_date": "YYYY-MM-DD",
      "affected_files": ["references/efficacy-56.md", ...],
      "proposed_changes": "string",
      "source_url": "string"
    }
  ],
  "case_studies": [
    {
      "case_name": "string",
      "date": "YYYY-MM-DD",
      "agency": "消費者庁|厚生労働省|都道府県薬務課|etc",
      "summary": "string",
      "violated_expressions": ["..."],
      "violated_laws": ["..."],
      "source_url": "string"
    }
  ]
}
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic package not installed. Run: pip install -r scripts/requirements.txt",
          file=sys.stderr)
    sys.exit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
REFERENCES_DIR = REPO_ROOT / "references"


SYSTEM_PROMPT = """あなたは日本の化粧品広告コンプライアンスを専門とする調査AIです。

タスク: 直近の景品表示法措置命令、薬機法関連通知、業界自主基準の改定を調査し、
化粧品広告レビュー用ナレッジベース(references/)への更新提案を構造化JSONとして出力する。

調査対象:
1. 消費者庁の措置命令(景品表示法違反)
2. 消費者庁の課徴金納付命令
3. 厚生労働省の薬機法関連通知・告示・事務連絡
4. 都道府県の薬事行政指導事例
5. 日本化粧品工業連合会の自主基準改定
6. 健康増進法違反の指導事例(美容関連食品など)

特に注目すべきカテゴリ:
- 化粧品・医薬部外品・サプリメントの広告
- インフルエンサー・アフィリエイトのステマ事例
- D2C・通販事業者のLP違反
- サロン・エステ・クリニックの広告違反

注意:
- 化粧品/美容関連の事例を優先する(医薬品単体、医療機器単体の事例は除外)
- 出典URLが明確でない情報は含めない
- 出典に基づかない推測・解釈は含めない
- 既存のreferences内容との重複を避ける(提案前に必ず既存内容と照合)

出力は **厳密にJSONのみ** とし、前後に説明文を付けないこと。"""


USER_PROMPT_TEMPLATE = """以下の条件で調査を実施し、references/への更新提案を構造化JSONで出力してください。

## 調査期間
過去 {lookback_days} 日間 ({since_date} 以降)

## 既存references要約

### efficacy-56.md (化粧品56効能効果)
{efficacy_summary}

### ng-expressions.md (NG表現データベース)
{ng_summary}

### keihyouhou.md (景表法チェックポイント)
{keihyouhou_summary}

### before-after-testimonials.md (ビフォーアフター・体験談)
{ba_summary}

## 出力スキーマ

```json
{{
  "generated_at": "ISO8601 timestamp",
  "lookback_days": {lookback_days},
  "summary": "今期の調査結果サマリー(1-3行)",
  "new_ng_patterns": [
    {{
      "expression": "NG表現の原文 or 典型例",
      "category": "A|B|C|D|E|F|G|H|I|J|K",
      "problem": "なぜNGか",
      "legal_basis": "薬機法66条 / 景表法5条1号 等",
      "rewrite_suggestion": "56効能内での代替表現",
      "source_url": "出典URL",
      "source_title": "出典タイトル",
      "source_date": "YYYY-MM-DD"
    }}
  ],
  "regulation_updates": [
    {{
      "law": "改正された法令名",
      "summary": "改正概要",
      "effective_date": "YYYY-MM-DD",
      "affected_files": ["references/xxx.md"],
      "proposed_changes": "references/への具体的な変更内容",
      "source_url": "出典URL"
    }}
  ],
  "case_studies": [
    {{
      "case_name": "事業者名/事案名",
      "date": "YYYY-MM-DD",
      "agency": "消費者庁|厚生労働省|...",
      "summary": "事案概要",
      "violated_expressions": ["違反とされた表現"],
      "violated_laws": ["景表法5条1号", ...],
      "source_url": "出典URL"
    }}
  ]
}}
```

該当する事例がなければ各配列は空配列 `[]` とし、JSONとして有効な形式で返してください。
出力は **JSONのみ** とし、それ以外のテキストは含めないでください。"""


# NGカテゴリ参照
VALID_CATEGORIES = {"A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"}


def summarize_file(filepath: Path, max_chars: int = 3000) -> str:
    """既存referenceファイルを要約用に切り出す"""
    if not filepath.exists():
        return "(未作成)"
    content = filepath.read_text(encoding="utf-8")
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + f"\n...(後略、全{len(content)}文字)"


def call_claude(client, system: str, user: str) -> str:
    """Claude API を web_search ツール付きで呼ぶ"""
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        system=system,
        messages=[{"role": "user", "content": user}],
        tools=[
            {
                "type": "web_search_20250305",
                "name": "web_search",
                "max_uses": 10,
            }
        ],
    )

    # text ブロックを連結
    text_parts = []
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            text_parts.append(block.text)
    return "\n".join(text_parts)


def extract_json(text: str) -> dict:
    """LLM出力からJSON部分を抽出"""
    # ```json ... ``` を剥がす
    cleaned = text.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1]
    if "```" in cleaned:
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    # 最初の { から最後の } までを抽出
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first == -1 or last == -1:
        raise ValueError("No JSON object found in response")

    json_text = cleaned[first:last + 1]
    return json.loads(json_text)


def validate_proposals(data: dict) -> tuple[dict, list[str]]:
    """提案を検証してフィルタリング。返り値は (clean_data, warnings)"""
    warnings = []
    cleaned = {
        "generated_at": data.get("generated_at", datetime.utcnow().isoformat()),
        "lookback_days": data.get("lookback_days", 31),
        "summary": data.get("summary", ""),
        "new_ng_patterns": [],
        "regulation_updates": [],
        "case_studies": [],
    }

    for item in data.get("new_ng_patterns", []):
        if not item.get("source_url"):
            warnings.append(f"Skipped NG pattern without source_url: {item.get('expression')}")
            continue
        if item.get("category") not in VALID_CATEGORIES:
            warnings.append(f"Invalid category for: {item.get('expression')}")
            item["category"] = "J"  # グレーゾーンに寄せる
        cleaned["new_ng_patterns"].append(item)

    for item in data.get("regulation_updates", []):
        if not item.get("source_url"):
            warnings.append(f"Skipped regulation update without source_url: {item.get('law')}")
            continue
        cleaned["regulation_updates"].append(item)

    for item in data.get("case_studies", []):
        if not item.get("source_url"):
            warnings.append(f"Skipped case study without source_url: {item.get('case_name')}")
            continue
        cleaned["case_studies"].append(item)

    return cleaned, warnings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="proposals.json")
    parser.add_argument("--lookback-days", type=int, default=31)
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    since_date = (datetime.utcnow() - timedelta(days=args.lookback_days)).strftime("%Y-%m-%d")

    user_prompt = USER_PROMPT_TEMPLATE.format(
        lookback_days=args.lookback_days,
        since_date=since_date,
        efficacy_summary=summarize_file(REFERENCES_DIR / "efficacy-56.md", 2000),
        ng_summary=summarize_file(REFERENCES_DIR / "ng-expressions.md", 3000),
        keihyouhou_summary=summarize_file(REFERENCES_DIR / "keihyouhou.md", 2000),
        ba_summary=summarize_file(REFERENCES_DIR / "before-after-testimonials.md", 1500),
    )

    print(f"[update_references] Calling Claude API (lookback={args.lookback_days}d, since={since_date})")

    try:
        response_text = call_claude(client, SYSTEM_PROMPT, user_prompt)
    except Exception as e:
        print(f"ERROR: Claude API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        data = extract_json(response_text)
    except Exception as e:
        print(f"ERROR: Failed to parse JSON from response: {e}", file=sys.stderr)
        print(f"Response was:\n{response_text[:2000]}", file=sys.stderr)
        # 空の提案を書いて非ゼロexitしない(workflow側でカウント0として扱う)
        Path(args.output).write_text(json.dumps({
            "generated_at": datetime.utcnow().isoformat(),
            "lookback_days": args.lookback_days,
            "summary": "JSON parse failed",
            "new_ng_patterns": [],
            "regulation_updates": [],
            "case_studies": [],
            "error": str(e),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(0)

    cleaned, warnings = validate_proposals(data)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    Path(args.output).write_text(
        json.dumps(cleaned, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    total = (
        len(cleaned["new_ng_patterns"])
        + len(cleaned["regulation_updates"])
        + len(cleaned["case_studies"])
    )
    print(f"[update_references] Generated {total} proposals "
          f"(ng={len(cleaned['new_ng_patterns'])}, "
          f"reg={len(cleaned['regulation_updates'])}, "
          f"cases={len(cleaned['case_studies'])})")
    print(f"[update_references] Output: {args.output}")


if __name__ == "__main__":
    main()
