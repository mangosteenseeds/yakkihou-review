# Contributing to yakkihou-review

このプロジェクトへの貢献を歓迎します!日本の化粧品・美容業界全体のコンプライアンス底上げを目指しています。

## 貢献の種類

### 1. NG表現の追加

実際の措置命令事例や行政指導事例に基づくNG表現の追加を歓迎します。

- 出典（措置命令の事業者名・年月、または公的ガイドライン）を必ず記載
- 修正案（56効能内での代替表現）も併せて提案
- 該当ファイル: `references/ng-expressions.md`

### 2. 法令改正への対応

厚生労働省告示、景品表示法、健康増進法等の改正に伴う references の更新。

- 出典の明示
- 改正の発効日を記載
- 該当ファイル: `references/efficacy-56.md`, `references/keihyouhou.md`

### 3. 業界自主基準の反映

日本化粧品工業連合会の自主基準改定への追従。

### 4. examples の追加

特定業態（クリニック、エステ、D2C、サロン等）向けのサンプル入出力。実在の広告物・社名は使用しないこと。

### 5. 多言語対応

英語・中国語等の対応（越境ECや海外向け事業者向け）。

### 6. 関連法のreferences拡充

- 健康増進法 (`references/kenkozoshin.md`)
- 特定商取引法 (`references/tokushoho.md`)
- 医師法・あはき法 (`references/iryo-shihou.md`)
- 個人情報保護法 (`references/personal-info.md`)

---

## PRの出し方

1. リポジトリをfork
2. featureブランチを作成: `git checkout -b feat/add-ng-pattern-xxx`
3. 変更を加える
4. テスト: 既存のexamplesで動作確認
5. コミット: メッセージは [Conventional Commits](https://www.conventionalcommits.org/) に従う
   - `feat: add NG pattern for "XX expression"`
   - `fix: update efficacy #36 wording`
   - `docs: clarify Step 0 in SKILL.md`
6. プッシュしてPR作成

## PR時のチェック事項

- [ ] 出典・根拠の明示
- [ ] CHANGELOG.md の更新
- [ ] examples で動作確認
- [ ] 実在の商品名・企業名を含んでいない（措置命令事例は公開情報のみ可）
- [ ] 法的判断を断定する表現を避けている

---

## 議論・提案

新規 references の追加、構造変更などは Issue で先に議論することを推奨します。

- `bug_report` — 既存内容の誤り
- `new_ng_pattern` — 新規NG表現の追加提案
- `regulation_update` — 法令改正に伴う更新提案

---

## コードオブコンダクト

本プロジェクトは Contributor Covenant に準拠します。誹謗中傷・差別的言動・特定事業者への攻撃的言及はお控えください。

---

## ライセンス

貢献いただいたコード・コンテンツは MIT License で公開されます。
