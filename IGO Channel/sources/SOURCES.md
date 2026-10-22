# 信頼できる定石ソースと検証ルール

## 3ソース検証ルール

1つの定石を動画化する前に、**主要手順（基本形）が3つ以上のソースで一致すること**を確認し、`sources/<joseki_id>.yaml` に記録する。

- 3ソースのうち **最低2カテゴリ以上** にまたがること（同じWikiを3ページ見ても1カテゴリ）。
- **カテゴリD（AI評価）は必須**。古い書籍の定石がAI時代に否定されているケースがあるため。
- 小さい変化（手順の入れ替え、1〜2手の別変化）は、AI評価で大損（目安: 目数損失 1.5目超）でなければOK。動画内で「変化」と明示する。
- ソース間で食い違う場合は動画化を保留するか、「旧定石 vs AI定石」の比較回にする。
- 書籍は手順の照合にのみ使い、図・文章は転載しない（著作権）。

## ソース一覧

### A. 書籍・公式（日本棋院 等）

| ソース | 用途 | 備考 |
|---|---|---|
| 日本棋院 出版の定石書（例: 定石事典・AI定石系の書籍） | 基本形の照合 | 購入した書籍のみ。書名・ページを記録 |
| [日本棋院](https://www.nihonkiin.or.jp) 公式講座・記事 | 用語・基本形 | |
| Kiseido "Dictionary of Basic Joseki"（石田芳夫） | 古典定石の照合 | AI以前。Dで再評価必須 |

### B. Web定石データベース

| ソース | URL | 備考 |
|---|---|---|
| OGS Joseki Explorer | https://online-go.com/joseki | コミュニティ編集。手ごとに「定石/悪手/トリック」タグ・出典つき |
| Josekipedia | https://www.josekipedia.com | 定石ツリー形式。手順の網羅確認に |
| Sensei's Library | https://senseis.xmp.net/?44PointLowApproach | 英語Wiki。星・小ケイマかかりのページから各変化へ辿れる |

### C. プロ実戦・棋譜

| ソース | URL | 備考 |
|---|---|---|
| Waltheri's Pattern Search | https://ps.waltheri.net | プロ棋譜での出現頻度・勝率。「実戦で本当に打たれているか」の確認 |
| プロ棋士の解説動画（例: 柳澤理志の囲碁教室） | https://www.youtube.com/@igoyanagi | 照合と最新見解の確認のみ。内容の転載はしない |

### D. AI評価（必須）

| ソース | URL | 備考 |
|---|---|---|
| KataGo | https://github.com/lightvector/KataGo | ローカルで解析を自動実行。各手の目数損失を記録 |
| KaTrain | https://github.com/sanderland/katrain | KataGo のGUI。人間レビュー用 |
| AI Sensei | https://ai-sensei.com | 必要に応じて照合 |

## 自動化の方針

- パイプラインは `status: verified` の yaml を持つ定石だけを動画化する。
- KataGo解析は自動で `ai_check` 欄を埋める。A〜Cの照合は自分がレビューして記入（＝勉強の工程）。
