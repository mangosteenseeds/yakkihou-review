# Claude Code 用 セットアップ指示書

このファイルの内容をそのまま Claude Code に投げてください。
Claude Code が以下を自動で完遂します:

1. 必要な CLI ツールの確認 (`gh`, `git`)
2. GitHub ユーザー名の自動取得
3. プレースホルダーの実ユーザー名への置換
4. Git 初期化とコミット
5. GitHub 上にパブリックリポジトリ作成
6. Actions の権限設定
7. `ANTHROPIC_API_KEY` の Secrets 登録 (対話的)
8. 初回 push
9. 月次更新 workflow の dry-run 動作確認

---

## 🤖 Claude Code への指示

以下を順番に実行してください。判断が必要な箇所は私(ユーザー)に確認してください。

### Step 1: 前提確認

```bash
# 必要ツールの確認
command -v gh && command -v git && command -v python3 || echo "MISSING TOOLS"

# gh の認証確認
gh auth status

# 認証中の GitHub ユーザー名取得
GH_USER=$(gh api user --jq .login)
echo "GitHub user: $GH_USER"
```

`gh auth status` で認証されていない場合は `gh auth login` を実行するよう案内してください。

### Step 2: プレースホルダー置換

このディレクトリ (`yakkihou-review/`) 内の以下のファイルに含まれる `<your-org>` プレースホルダーを、Step 1 で取得した `$GH_USER` に置換してください:

- `README.md`
- `SETUP.md` (もし `<your-org>` を含むなら)

`sed -i` を使ってください (macOS の場合は `sed -i ''`)。

確認: 置換後、`grep -r "your-org" .` で残存がないことを確認してください。

### Step 3: bootstrap.sh の実行

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

`bootstrap.sh` が対話的に以下を質問します:
1. リポジトリ名 (デフォルト: `yakkihou-review`)
2. リポジトリ説明
3. ANTHROPIC_API_KEY (シークレット入力)
4. 月次更新の dry-run を即時実行するか

すべての処理が成功したら、リポジトリ URL を表示してください。

### Step 4: 動作確認

```bash
# CI が走ったことを確認
gh run list --limit 5

# 月次更新を手動 dispatch (dry-run)
gh workflow run monthly-update.yml -f lookback_days=7 -f dry_run=true

# 実行ログを watch
sleep 10
gh run watch
```

完了したら、artifact ( `proposals.json` ) をダウンロードして内容を確認してください:

```bash
gh run download --name update-artifacts-<run-id>
cat proposals.json | python3 -m json.tool | head -50
```

### Step 5: 完了報告

以下をユーザーに報告してください:
- リポジトリ URL
- 初回 CI の通過状況
- dry-run の結果サマリ (proposals.json の件数)
- 次のアクション (本番実行の cron スケジュール、月初に PR が自動起票される旨)

---

## エラーハンドリング指針

- `gh auth status` 失敗 → `gh auth login --web` を実行するよう促す
- `gh repo create` で既存リポジトリ名衝突 → ユーザーに別名を確認
- Secrets 登録失敗 → リポジトリの Settings リンクを表示し手動登録を案内
- ワークフロー失敗 → ログを取得して原因を分析、修正後 push

判断が割れる場面では、ユーザーに簡潔に選択肢を提示してください。

---

## 注意事項

- このリポジトリは **パブリック公開** です。コミット前に `.env` や個人情報が含まれていないか `git status` で確認してください
- `ANTHROPIC_API_KEY` は **Secrets経由でのみ** リポジトリに渡してください。コードや README にハードコードしないでください
- `gh secret set` は標準入力で値を受け取れます (`echo "$KEY" | gh secret set ANTHROPIC_API_KEY`)
