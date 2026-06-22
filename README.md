# yakkihou-review

> 日本の **薬機法（医薬品医療機器等法）** および **景品表示法** の観点から、化粧品・美容関連の広告物・LP・SNS投稿・販促資料を自動レビューする Claude Code 用 Skill。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://docs.claude.com/en/docs/claude-code)

---

## 🎯 何ができるか

化粧品メーカー・サロン・美容クリニック・D2Cブランド・広告代理店向けに、以下を自動チェックします:

- **NG表現の検出**（医薬品的効能・身体構造変化・絶対的効果保証など）
- **化粧品 56効能効果との照合**（厚生労働省告示）
- **景表法チェック**（優良誤認・有利誤認・No.1表示・体験談・ステマ規制）
- **ビフォーアフター写真・症例写真の取扱い判定**
- **修正案の自動生成**（56効能の範囲内での代替表現）

公開前のドラフトレビュー、既存資産の棚卸し、サロン・代理店への配布物チェックに使えます。

---

## ⚠️ 重要な免責事項

このSkillは**機械的な一次レビューツール**です。最終的な適法判断ではありません。

- 重要な広告・大規模な販促展開の前には、**薬事に強い行政書士・弁護士、または都道府県薬務課**へ確認してください
- 表現の違法性は文脈で変わります。前後の文章・画像・受け手のセグメントとの組合せで最終判断してください
- 法令・ガイドラインは更新されます。`references/` の継続的なメンテナンスが必要です

本Skillおよびその利用に起因する一切の損害について、コントリビュータは責任を負いません。

---

## 🚀 インストール

### Claude Code（推奨）

#### ユーザーグローバル

```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
git clone https://github.com/mangosteenseeds/yakkihou-review.git
```

#### プロジェクトローカル

```bash
mkdir -p .claude/skills
cd .claude/skills
git clone https://github.com/mangosteenseeds/yakkihou-review.git
```

`.claude/skills/yakkihou-review/SKILL.md` が認識されれば自動でロードされます。Claude Code を再起動してください。

### Claude.ai Project

1. Claude.ai で新規プロジェクトを作成
2. プロジェクトナレッジに以下のファイルをアップロード:
   - `SKILL.md`
   - `references/efficacy-56.md`
   - `references/ng-expressions.md`
   - `references/keihyouhou.md`
   - `references/before-after-testimonials.md`
3. システムプロンプトに「薬機法レビューが必要な原稿が来たら、SKILL.md の手順に従ってレビューする」と明示

### 自分でリポジトリを公開する場合

Claude Code に `CLAUDE_CODE_PROMPT.md` の内容を投げれば、`bootstrap.sh` が対話的に GitHub リポジトリ作成・Secrets 登録・Actions 設定まで自動で完遂します。詳細は [`SETUP.md`](./SETUP.md) を参照してください。

---

## 💡 使い方

Claude Code 起動後、以下のように呼び出します:

```
新作美容液LPの原稿を作ったので、薬機法レビューしてほしい。
製品分類は一般化粧品、媒体はLP、効能評価試験データはなし。

[原稿]
シミが消える!驚異の若返り美容液。皮膚科医も推薦。
3日で肌が変わる、本物の効果をあなたに。
...
```

Skillが自動起動し、以下のフォーマットでレビュー結果を返します:

```
# 薬機法・景表法レビュー結果

## サマリー
- 製品分類: 一般化粧品
- 媒体: LP
- 重大NG: 5件 / グレー: 2件 / 確認事項: 1件

## 🔴 違法性が高い表現（即時修正必須）
| 該当箇所 | 問題点 | 法的根拠 | 修正案 |
|---------|-------|---------|-------|
| "シミが消える" | 効能範囲外 | 薬機法66条 | "日やけによるシミ、ソバカスを防ぐ"(要医薬部外品) |
...
```

詳細は [`examples/`](./examples/) を参照してください。

---

## 📁 ディレクトリ構成

```
yakkihou-review/
├── SKILL.md                                    # Skill エントリポイント
├── references/
│   ├── efficacy-56.md                          # 化粧品56効能効果（厚労省告示）
│   ├── ng-expressions.md                       # NG表現データベース
│   ├── keihyouhou.md                           # 景表法チェックポイント
│   └── before-after-testimonials.md            # ビフォーアフター・体験談規制
├── examples/
│   ├── sample-input-lp.md                      # サンプル入力（LP原稿）
│   └── sample-output-review.md                 # サンプル出力（レビュー結果）
├── scripts/
│   ├── update_references.py                    # Claude APIで先月以降の事例を調査
│   ├── apply_proposals.py                      # 提案をreferences/へ反映
│   ├── update_changelog.py                     # CHANGELOG自動追記
│   ├── validate_skill.py                       # CI: SKILL.md検証
│   ├── validate_references.py                  # CI: references/検証
│   ├── requirements.txt
│   └── README.md                               # パイプライン仕様書
├── .github/
│   ├── workflows/
│   │   ├── monthly-update.yml                  # 月次cron自動更新
│   │   └── ci.yml                              # PR/push時の検証
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── new_ng_pattern.md
│   │   └── regulation_update.md
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── dependabot.yml
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── SETUP.md                                    # リポジトリ公開・運用手順
```

---

## 🔄 法令・ガイドラインの更新ポリシー

このSkillの精度は `references/` の鮮度に依存します。以下のタイミングで更新を推奨します:

| 更新トリガー | 頻度の目安 | 影響範囲 |
|---|---|---|
| 厚生労働省告示・通知の改正 | 不定期 | `efficacy-56.md`, `ng-expressions.md` |
| 景品表示法施行令の改正 | 不定期 | `keihyouhou.md` |
| 消費者庁の措置命令事例 | 月次 | `ng-expressions.md`, `case-studies.md` |
| 業界自主基準（日化工連）の改定 | 不定期 | 全reference |

### 🤖 月次自動更新パイプライン

本リポジトリは **GitHub Actions + Claude API** による月次自動更新を備えています:

- 毎月1日 09:00 JST に `.github/workflows/monthly-update.yml` が起動
- 過去31日分の措置命令・通知を Claude API + web_search で調査
- 自動的に PR を起票（ラベル: `auto-update`, `regulation`, `needs-human-review`）
- 人間レビューを経てマージ

詳細は [`SETUP.md`](./SETUP.md) および [`scripts/README.md`](./scripts/README.md) を参照してください。

PR・Issue 歓迎です。[`CONTRIBUTING.md`](./CONTRIBUTING.md) を参照してください。

---

## 🤝 コントリビューション

このプロジェクトは日本の化粧品・美容業界全体のコンプライアンス底上げを目的としています。以下を歓迎します:

- 新規NG表現の追加（実際の措置命令事例ベース）
- references の法令改正対応
- 多言語化（英語、中国語など、越境ECに対応）
- examples の追加（特定業態向け: クリニック、エステ、D2C等）
- 関連法（健康増進法、特商法、医師法）の references 追加

詳細は [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

---

## 🌐 関連リソース

- [医薬品等適正広告基準（厚生労働省）](https://www.mhlw.go.jp/)
- [化粧品の効能の範囲の改正について（薬食審査発0721第1号）](https://www.mhlw.go.jp/)
- [景品表示法（消費者庁）](https://www.caa.go.jp/)
- [ステルスマーケティング規制（消費者庁）](https://www.caa.go.jp/)
- [日本化粧品工業連合会](https://www.jcia.org/)

---

## 📜 ライセンス

[MIT License](./LICENSE)

このSkillはAIが生成する判定結果について何ら保証するものではありません。利用は自己責任でお願いします。

---

## ✨ Credits

Built as a Claude Code Skill. Maintained by the cosmetics compliance community.
