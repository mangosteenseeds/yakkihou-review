# Changelog

このプロジェクトの全ての変更を記録します。

フォーマットは [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に準拠し、
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に従います。

## [Unreleased]

### Added (2026-08-01 - automated)
- 1 new NG expression(s) appended to `references/ng-expressions.md`
- 1 case study/studies appended to `references/case-studies.md`
- 1 pending regulation update(s) in `references/REGULATION-UPDATES-PENDING.md`


## [1.1.0] - 2026-06-22

### Added
- **月次自動更新パイプライン** (`.github/workflows/monthly-update.yml`)
  - Claude API (claude-opus-4-8) + web_search による先月以降の措置命令・通知の自動調査
  - 構造化JSON提案の生成と references/ への自動反映
  - PR の自動起票 (`auto-update`, `regulation`, `needs-human-review` ラベル付き)
  - dry-run モード対応
- **CI workflow** (`.github/workflows/ci.yml`)
  - SKILL.md frontmatter 検証
  - references/ 構成検証
  - YAML lint
  - 内部組織名のリーク検出
- **scripts/** ディレクトリ
  - `update_references.py` - Claude API 呼び出しと提案生成
  - `apply_proposals.py` - 提案を references/ に反映
  - `update_changelog.py` - CHANGELOG.md 自動更新
  - `validate_skill.py`, `validate_references.py` - CI検証
  - `requirements.txt`
  - `README.md` - パイプライン仕様書
- **SETUP.md** - リポジトリ公開と運用開始の手順書
- references/REGULATION-UPDATES-PENDING.md は実行時に動的生成 (pending な法令改正を集約)
- references/case-studies.md は実行時に動的生成 (措置命令事例集)

### Changed
- `.gitignore` に `references/local-*.md` (private customization 用) を追加済み

## [1.0.0] - 2026-06-22

### Added
- 初回リリース
- `SKILL.md` - Skill エントリポイント(6 Step レビュープロセス)
- `references/efficacy-56.md` - 化粧品56効能効果(厚労省告示 薬食審査発0721第1号 ベース)
- `references/ng-expressions.md` - NG表現データベース(11カテゴリ)
- `references/keihyouhou.md` - 景表法チェックポイント
- `references/before-after-testimonials.md` - ビフォーアフター・症例写真規制
- `examples/` - サンプル入出力
- `.github/` - Issue/PRテンプレート
- MIT License + 法的助言ではない旨の追加免責
- CONTRIBUTING.md
