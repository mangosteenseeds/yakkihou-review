# Automation Scripts

GitHub Actions から呼ばれる、references の自動更新パイプライン用スクリプト群。

## ファイル構成

| Script | 役割 |
|--------|------|
| `update_references.py` | Claude API + web_search で先月以降の措置命令・通知を調査し、構造化JSONとして提案を出力 |
| `apply_proposals.py` | 提案JSONを references/*.md へ反映、PR本文を生成 |
| `update_changelog.py` | CHANGELOG.md の `[Unreleased]` セクションを更新 |
| `validate_skill.py` | CI用: SKILL.md frontmatter検証 |
| `validate_references.py` | CI用: references/ 構成検証 |
| `requirements.txt` | Python依存 |

## 動作フロー

```
[cron: 毎月1日] or [workflow_dispatch]
   ↓
update_references.py
   - 既存 references/*.md を読み込み
   - Claude API (claude-opus-4-8) を web_search ツール付きで呼ぶ
   - 「先月以降の景表法措置命令・薬機法通知」を調査
   - 構造化JSON (proposals.json) を出力
   ↓
[件数チェック: proposal_count > 0 なら続行]
   ↓
apply_proposals.py
   - NG表現: references/ng-expressions.md 末尾に「🆕 自動追加」セクション追加
   - 事例:    references/case-studies.md に追記(なければ作成)
   - 法令改正: references/REGULATION-UPDATES-PENDING.md に書き出し(人間対応)
   - pr_body.md を生成
   ↓
update_changelog.py
   - CHANGELOG.md の [Unreleased] に件数サマリを追記
   ↓
peter-evans/create-pull-request
   - ブランチ作成: auto/monthly-update-YYYY-MM-DD-{run_id}
   - PR作成: ラベル `auto-update`, `regulation`, `needs-human-review`
   ↓
[人間レビュー → マージ]
```

## 必要なシークレット

GitHubリポジトリの Settings > Secrets and variables > Actions に登録:

| Name | 内容 |
|------|------|
| `ANTHROPIC_API_KEY` | Claude API キー |

`GITHUB_TOKEN` は GitHub Actions が自動付与するため、設定不要(`peter-evans/create-pull-request@v6` が利用)。

## 手動実行

```bash
# 環境変数設定
export ANTHROPIC_API_KEY=sk-ant-...

# 依存インストール
pip install -r scripts/requirements.txt

# 提案生成 (デフォルト: 過去31日)
python scripts/update_references.py --output proposals.json --lookback-days 31

# 反映
python scripts/apply_proposals.py --input proposals.json --pr-body-out pr_body.md

# CHANGELOG更新
python scripts/update_changelog.py --proposals proposals.json
```

ローカル実行で確認後、git diff で変更を確認しコミット。

## トラブルシューティング

### JSON解析エラー

`update_references.py` で Claude の応答がJSONとして解析できない場合、空配列の proposals.json を書いて exit 0 する。これにより workflow は失敗せず、その月のPRは作成されない。

### API ratelimit

Anthropic API のレート制限に達した場合、workflow は失敗する。月1回の実行なので通常は問題ない。

### 過剰な提案

`update_references.py` の SYSTEM_PROMPT で「化粧品/美容関連の事例を優先」「出典URLが明確でないものは含めない」と縛っている。それでも誤検出が多い場合は、`validate_proposals()` のフィルタを強化する。

## 拡張アイデア

- 検索ソースを限定する allowlist (e.g., caa.go.jp, mhlw.go.jp)
- 既存 ng-expressions.md と重複する提案を embedding でフィルタ
- 月次ではなく週次への切り替え (cron変更のみ)
- Slack/Discord 通知 (新規措置命令検出時)
- 複数の reference リポジトリへの fan-out (関連法ごとに分割した場合)
