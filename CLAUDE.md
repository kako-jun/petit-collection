# petit-collection

写真や手描き絵、観光スタンプを「自分のコレクション」に変えて台紙へ貼る、
ローカル完結の Web アプリです。実装前の今は、README と docs を先に整え、
何が `petit-collection` 単独で進められて、何が他プロジェクト待ちかを明確にする段階です。

## ドキュメント

| ファイル | 内容 | 言語 |
|---|---|---|
| `README.md` | エンドユーザー向け概要 | 英語 |
| `docs/overview.md` | 何を作るか、どういう体験を狙うか | 英語 |
| `docs/spec.md` | ドメインモデルと MVP の契約 | 英語 |
| `docs/roadmap.md` | 実装フェーズの大枠 | 英語 |
| `docs/research-notes.md` | 競合・依存先・ブロッカー観察 | 英語 |
| `docs/issue-backlog.md` | Issue 下書き、優先度、依存関係 | 英語 |
| `CLAUDE.md` | AI 向け内部メモ | 日本語 |

## 現在の構造

```
docs/
├── issue-backlog.md
├── overview.md
├── research-notes.md
├── roadmap.md
└── spec.md

scripts/
└── reverse_stamp_poc.py
```

## 設計メモ

- HyperCard 的にする対象は **個々のシールではなく帳面ページ**
- 情報設計は **Library** と **Book** に分ける
- `Library` は実務寄り、`Book` は体験寄り
- まずは一般ユーザーが触れる MVP を定義し、authoring system 化は後ろ
- 「何でもできるカード帳」を急がず、「貼る/剥がす/めくる」が気持ちいい最小ループを先に作る

## ブロッカー整理の原則

- `petit-collection` 単独で進む仕事は Issue を前倒しする
- 他リポ待ちは `docs/issue-backlog.md` に依存関係を明記する
- 「待ち」と言っても、完全停止ではなく **先に契約・UI・ダミー経路を作れるか** を必ず検討する

## 実装ルール

- 実装前でも docs と backlog は更新する
- 他プロジェクト依存の話は、Issue に「Blocked by / Informed by」を書く
- Python を使う検証が必要なら `uv run python3` を使う
- GitHub Issue 化ができない環境では、まず `docs/issue-backlog.md` を正本として更新する
- `scripts/reverse_stamp_poc.py` は #13 の実験用。`uv run --with opencv-python-headless --with numpy python3 ...` で再現する
