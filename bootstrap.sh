#!/usr/bin/env bash
#
# yakkihou-review bootstrap script
#
# このスクリプトは以下を自動実行します:
# 1. プレースホルダー置換
# 2. git init とコミット
# 3. GitHub にパブリックリポジトリ作成
# 4. Actions の権限設定 (write + PR作成許可)
# 5. ANTHROPIC_API_KEY を Secrets に登録
# 6. 初回 push
# 7. (オプション) 月次更新 workflow の dry-run 実行
#
# 前提:
# - gh CLI が認証済み (gh auth status)
# - git がインストール済み
# - このスクリプトは yakkihou-review/ ディレクトリ直下で実行する

set -euo pipefail

# ============================================================
# Helpers
# ============================================================

color_info()  { printf "\033[1;34m[INFO]\033[0m  %s\n" "$*"; }
color_ok()    { printf "\033[1;32m[OK]\033[0m    %s\n" "$*"; }
color_warn()  { printf "\033[1;33m[WARN]\033[0m  %s\n" "$*"; }
color_err()   { printf "\033[1;31m[ERROR]\033[0m %s\n" "$*" >&2; }

confirm() {
  local prompt="${1:-Continue?}"
  local default="${2:-y}"
  local reply
  if [[ "$default" == "y" ]]; then
    read -r -p "$prompt [Y/n]: " reply
    reply="${reply:-y}"
  else
    read -r -p "$prompt [y/N]: " reply
    reply="${reply:-n}"
  fi
  [[ "$reply" =~ ^[Yy] ]]
}

# sed -i は macOS と Linux で挙動が違う
sed_inplace() {
  if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "$@"
  else
    sed -i "$@"
  fi
}

# ============================================================
# Step 0: 前提確認
# ============================================================

color_info "Checking prerequisites..."

for cmd in git gh python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    color_err "$cmd is not installed."
    exit 1
  fi
done

if ! gh auth status >/dev/null 2>&1; then
  color_err "gh CLI is not authenticated. Run: gh auth login"
  exit 1
fi

GH_USER=$(gh api user --jq .login)
color_ok "Authenticated as GitHub user: $GH_USER"

# このスクリプトのある場所が SKILL.md と同階層であることを確認
if [[ ! -f "SKILL.md" ]] || [[ ! -d "references" ]]; then
  color_err "This script must be run from the yakkihou-review/ root directory."
  color_err "Expected to find SKILL.md and references/ in $(pwd)"
  exit 1
fi

# ============================================================
# Step 1: リポジトリ名と説明を確認
# ============================================================

DEFAULT_REPO_NAME="yakkihou-review"
read -r -p "Repository name [${DEFAULT_REPO_NAME}]: " REPO_NAME
REPO_NAME="${REPO_NAME:-$DEFAULT_REPO_NAME}"

DEFAULT_DESC="Japanese cosmetics advertising compliance review skill for Claude Code (薬機法・景表法レビュー)"
read -r -p "Repository description [${DEFAULT_DESC}]: " REPO_DESC
REPO_DESC="${REPO_DESC:-$DEFAULT_DESC}"

DEFAULT_VISIBILITY="public"
read -r -p "Visibility (public/private) [${DEFAULT_VISIBILITY}]: " REPO_VIS
REPO_VIS="${REPO_VIS:-$DEFAULT_VISIBILITY}"

color_info "Repository will be created as: $GH_USER/$REPO_NAME ($REPO_VIS)"
if ! confirm "Proceed?"; then
  color_warn "Aborted by user."
  exit 0
fi

# ============================================================
# Step 2: プレースホルダー置換
# ============================================================

color_info "Replacing placeholders..."

# README.md, SETUP.md, CODEOWNERS 内の <your-org> を実ユーザー名に置換
for f in README.md SETUP.md .github/CODEOWNERS; do
  if [[ -f "$f" ]] && grep -q "<your-org>" "$f" 2>/dev/null; then
    sed_inplace "s|<your-org>|$GH_USER|g" "$f"
    color_ok "Updated $f"
  fi
done

# プレースホルダー残存チェック (.md と CODEOWNERS の両方)
if grep -rn "<your-org>" . --include="*.md" 2>/dev/null \
   || grep -n "<your-org>" .github/CODEOWNERS 2>/dev/null; then
  color_warn "Some <your-org> placeholders may remain. Please review."
fi

# ============================================================
# Step 3: Git 初期化
# ============================================================

if [[ -d ".git" ]]; then
  color_warn ".git already exists. Skipping git init."
else
  color_info "Initializing git repository..."
  git init -b main >/dev/null
  color_ok "git init done"
fi

# .git に含めないファイルを確認 (一応)
if [[ -f ".env" ]]; then
  color_err ".env file found in repository. This should NOT be committed."
  color_err "Move it outside the repo or delete it before continuing."
  exit 1
fi

color_info "Staging files..."
git add .
if git diff --cached --quiet; then
  color_warn "No changes to commit."
else
  git commit -m "feat: initial release v1.1.0

- yakkihou-review skill for Claude Code
- 薬機法 (Pharmaceutical Affairs Act) and 景表法 (Premiums and Representations Act) review
- Includes 化粧品56効能 reference, NG expression database, and case study framework
- Automated monthly references update pipeline via GitHub Actions + Claude API" >/dev/null
  color_ok "Initial commit created"
fi

# ============================================================
# Step 4: GitHub リポジトリ作成
# ============================================================

if gh repo view "$GH_USER/$REPO_NAME" >/dev/null 2>&1; then
  color_warn "Repository $GH_USER/$REPO_NAME already exists."
  if confirm "Use existing repository and push to it?"; then
    if ! git remote get-url origin >/dev/null 2>&1; then
      git remote add origin "https://github.com/$GH_USER/$REPO_NAME.git"
    fi
  else
    color_warn "Aborted. Choose a different repo name and re-run."
    exit 0
  fi
else
  color_info "Creating GitHub repository: $GH_USER/$REPO_NAME ($REPO_VIS)"
  gh repo create "$REPO_NAME" \
    "--$REPO_VIS" \
    --description "$REPO_DESC" \
    --source=. \
    --remote=origin \
    --push=false
  color_ok "Repository created"
fi

# ============================================================
# Step 5: Actions 権限設定
# ============================================================

color_info "Configuring Actions permissions (write + PR creation)..."

# Actions が PR を作成できるよう設定
gh api -X PUT "repos/$GH_USER/$REPO_NAME/actions/permissions/workflow" \
  -f default_workflow_permissions='write' \
  -F can_approve_pull_request_reviews=true \
  >/dev/null

color_ok "Workflow permissions configured: write + PR creation allowed"

# ============================================================
# Step 6: ANTHROPIC_API_KEY を Secrets に登録
# ============================================================

color_info "Setting up ANTHROPIC_API_KEY..."

if gh secret list --repo "$GH_USER/$REPO_NAME" 2>/dev/null | grep -q "^ANTHROPIC_API_KEY"; then
  color_ok "ANTHROPIC_API_KEY already exists in repository secrets."
  if confirm "Overwrite?" "n"; then
    SET_KEY=1
  else
    SET_KEY=0
  fi
else
  SET_KEY=1
fi

if [[ "$SET_KEY" == "1" ]]; then
  echo
  echo "Please paste your Anthropic API key (input hidden):"
  read -r -s ANTHROPIC_API_KEY
  echo
  if [[ -z "$ANTHROPIC_API_KEY" ]]; then
    color_warn "Empty key provided. Skipping Secrets registration."
    color_warn "You will need to set ANTHROPIC_API_KEY manually before the monthly workflow can run."
  else
    echo "$ANTHROPIC_API_KEY" | gh secret set ANTHROPIC_API_KEY --repo "$GH_USER/$REPO_NAME"
    unset ANTHROPIC_API_KEY
    color_ok "ANTHROPIC_API_KEY registered in repository secrets"
  fi
fi

# ============================================================
# Step 7: Push
# ============================================================

color_info "Pushing to GitHub..."
git push -u origin main
color_ok "Pushed to https://github.com/$GH_USER/$REPO_NAME"

# ============================================================
# Step 8: 動作確認用 dry-run
# ============================================================

echo
if confirm "Run the monthly-update workflow now (dry-run, lookback=7 days)?"; then
  color_info "Triggering workflow_dispatch (dry-run mode)..."

  # workflow がリモートに反映されるのを待つ
  sleep 5

  if gh workflow run monthly-update.yml \
       --repo "$GH_USER/$REPO_NAME" \
       -f lookback_days=7 \
       -f dry_run=true; then
    color_ok "Workflow dispatched"
    sleep 8
    color_info "Recent workflow runs:"
    gh run list --repo "$GH_USER/$REPO_NAME" --limit 3
    echo
    color_info "Watch the run with:"
    echo "  gh run watch --repo $GH_USER/$REPO_NAME"
  else
    color_warn "Failed to dispatch workflow. You may need to wait a moment for GitHub to register the workflow files."
    color_warn "Try manually later:"
    echo "  gh workflow run monthly-update.yml --repo $GH_USER/$REPO_NAME -f lookback_days=7 -f dry_run=true"
  fi
fi

# ============================================================
# Done
# ============================================================

echo
color_ok "=========================================="
color_ok "  Setup complete!"
color_ok "=========================================="
echo
echo "Repository:        https://github.com/$GH_USER/$REPO_NAME"
echo "Actions:           https://github.com/$GH_USER/$REPO_NAME/actions"
echo "Settings:          https://github.com/$GH_USER/$REPO_NAME/settings"
echo
echo "Next steps:"
echo "  - Review the README.md and edit if needed"
echo "  - Optional: Add branch protection on 'main' (Settings → Branches)"
echo "  - The monthly cron will trigger on the 1st of each month at 09:00 JST"
echo "  - To trigger manually: gh workflow run monthly-update.yml --repo $GH_USER/$REPO_NAME"
echo
