# Setup Guide

このSkillをオープンソースリポジトリとして公開し、月次自動更新パイプラインを稼働させるまでの手順。

---

## 🚀 ワンライナーセットアップ（推奨）

Claude Code に `CLAUDE_CODE_PROMPT.md` を投げて自動セットアップする方法が最速です。または手動で:

```bash
cd yakkihou-review
./bootstrap.sh
```

これだけで以下が自動実行されます:
- プレースホルダー (`mangosteenseeds`) の実 GitHub ユーザー名への置換
- git 初期化と初回コミット
- GitHub にパブリックリポジトリ作成
- Actions の権限設定 (write + PR作成許可)
- `ANTHROPIC_API_KEY` の Secrets 登録 (対話的入力)
- 初回 push
- 動作確認用 dry-run の手動 dispatch

完了後、以下の手動セクションは飛ばして「**5. 公開後の運用**」へ進んでください。

---

## 手動セットアップ手順

`bootstrap.sh` を使わず手動で進める場合の手順:

## 1. GitHubリポジトリ作成

```bash
cd path/to/unzipped/yakkihou-review
git init
git add .
git commit -m "feat: initial release v1.0.0"
git branch -M main

# GitHub CLI を使う場合
gh repo create yakkihou-review --public --source=. --remote=origin --push

# Web UIから作る場合
git remote add origin https://github.com/mangosteenseeds/yakkihou-review.git
git push -u origin main
```

---

## 2. Secrets 設定

GitHub リポジトリの **Settings → Secrets and variables → Actions → New repository secret** で以下を登録:

| Name | 内容 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API キー (https://console.anthropic.com で発行) |

`GITHUB_TOKEN` は GitHub Actions が自動付与するので不要。

---

## 3. リポジトリ設定

### Actions の権限

Settings → Actions → General → Workflow permissions:

- ✅ "Read and write permissions"
- ✅ "Allow GitHub Actions to create and approve pull requests"

これにより `peter-evans/create-pull-request` が PR を起票できる。

### ブランチ保護(推奨)

Settings → Branches → Add rule (for `main`):

- ✅ Require pull request before merging
- ✅ Require status checks (CI)
- ✅ Require approval (1 reviewer)

自動更新PRも人間レビュー必須にする。

---

## 4. 動作確認

### CIの動作確認

PRを試しに1つ出して、CIが通ることを確認:

```bash
git checkout -b test/ci-trigger
echo "" >> README.md
git commit -am "test: trigger ci"
git push origin test/ci-trigger
gh pr create --fill
```

### 月次更新の手動実行(dry-run推奨)

Actions タブ → "Monthly References Update" → "Run workflow":

- `lookback_days`: 7 (短めにして動作確認)
- `dry_run`: true (PR作成しない)

ログを確認し、proposals.json が artifact としてダウンロード可能になっていればOK。

問題なければ `dry_run: false` で本番実行。

---

## 5. 公開後の運用

### マンスリーレビュー

毎月のPRに対して以下を実施:

1. 提案された各NG表現の出典URLを実際に確認
2. 既存 references との重複・矛盾の確認
3. `REGULATION-UPDATES-PENDING.md` の内容を該当ファイルに手動マージ
4. case-studies.md の事業者名が公表情報であることを確認
5. 修正案が56効能内に収まっているか確認
6. 必要に応じて薬事専門家へ確認依頼
7. マージ → `REGULATION-UPDATES-PENDING.md` から該当エントリを削除

### バージョンタグ

四半期ごと程度に release を切る:

```bash
git tag -a v1.1.0 -m "Quarterly release with N new NG patterns"
git push origin v1.1.0
gh release create v1.1.0 --generate-notes
```

### コントリビューター対応

- Issue: 法令改正・新規NG表現の提案 → ラベル別管理
- PR: マニュアル提案はテンプレ通りの根拠提示を求める

---

## 6. プライベートカスタマイズ(オプション)

組織固有の運用は、forkして以下を追加:

```
yakkihou-review-private/
├── (yakkihou-reviewのfork)
└── references/
    ├── local-brand-guideline.md   # 自社ブランドトーン
    ├── local-product-lines.md     # 自社製品の効能境界
    └── local-customer-segments.md # 対象顧客セグメント
```

`.gitignore` で `references/local-*.md` を除外してあるので、これらは public へは出ない。

upstream(公開リポジトリ)の更新を定期的に取り込む:

```bash
git remote add upstream https://github.com/mangosteenseeds/yakkihou-review.git
git fetch upstream
git merge upstream/main
```

---

## 7. API使用量の目安

- 月1回の `update_references.py` 実行で **約 $0.50〜$2.00** (web_search使用、レスポンス最大16k tokens)
- CIは `validate_*.py` のみで Claude API は使わない (無料)
- 想定年間コスト: **$6〜$24**

---

## トラブルシューティング

### PRが作成されない
- Settings → Actions → "Allow GitHub Actions to create and approve pull requests" が ON か確認
- workflow ログで `peter-evans/create-pull-request` のエラー詳細を確認

### Claude API がタイムアウトする
- `update_references.py` の `max_uses: 10` を減らす (5に下げる等)
- `lookback_days` を減らす (調査範囲を狭める)

### 重複提案が多い
- 既存 `ng-expressions.md` の内容が長くなりすぎてプロンプトに収まっていない可能性
- `summarize_file()` の max_chars を増やす、または embedding ベースの重複排除を追加
