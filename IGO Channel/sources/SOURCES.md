# 信頼できる定石ソースと検証ルール

## 3ソース検証ルール

1つの定石を動画化する前に、**主要手順（基本形）が3つ以上のソースで一致すること**を確認し、`sources/<joseki_id>.yaml` に記録する。

- 3ソースのうち **最低2カテゴリ以上** にまたがること（同じサイトの別ページは1ソース）。
- **AI評価（カテゴリD）は公開前に必須**。古い定石がAI時代に否定されているケースがあるため。
- 小さい変化（手順の入れ替え、1〜2手の別変化）は、AI評価で大損（目安: 目数損失 1.5目超）でなければOK。動画内で「変化」と明示する。
- ソース間で食い違う場合は動画化を保留するか、「旧定石 vs AI定石」の比較回にする。
- ソースの図・文章は転載しない（著作権）。手順（座標）の照合と、要点を自分の言葉で書くことにとどめる。

定石書は手元にないため、当面は公開Webソースで3ソースをそろえる。書籍を買ったらカテゴリAに追加する。

## ソース一覧

### A. 日本語の定石解説（書籍の代わり）

| 略号 | ソース | URL | 使い方 |
|---|---|---|---|
| GJ | 囲碁定石研究 | https://gojoseki.shogidb2.com/hoshi/kogeimagakari/ | 日本語の定石名と候補手。ページ内の `data-wgo` にSGFがある |
| IB | 初心者〜初段までの囲碁定石 | https://igobook.info/ | SGF＋悪手の解説。級位者がつまずく点の確認 |
| PN | パンダネット 囲碁入門 | https://www.pandanet.co.jp/igonyumon/11-02.htm | 間違いと咎め方の解説（入門講座） |

### B. 海外のWeb定石DB

| 略号 | ソース | URL | 使い方 |
|---|---|---|---|
| OGS | OGS Joseki Explorer | https://online-go.com/joseki | 手ごとに IDEAL / GOOD / MISTAKE / TRICK の判定と出典。API `https://online-go.com/oje/position?id=<node>` で自動取得できる |
| SL | Sensei's Library | https://senseis.xmp.net/?44PointLowApproach | 英語Wiki。プロでの頻度（Waltheri）とAI評価（KaTrain）の数値つき |
| JP | Josekipedia | https://www.josekipedia.com | 定石ツリー。手順の網羅確認に |

### C. プロ実戦・棋譜

| ソース | URL | 使い方 |
|---|---|---|
| Waltheri's Pattern Search | https://ps.waltheri.net | プロ棋譜での出現頻度。「実戦で本当に打たれているか」の確認 |
| 碁DB | https://godb.shogidb2.com | 日本語の棋譜DB（GJの姉妹サイト） |
| プロ棋士の解説動画（例: 柳澤理志の囲碁教室） | https://www.youtube.com/@igoyanagi | 照合と最新見解の確認のみ。内容の転載はしない |

### D. AI評価（公開前に必須）

| ソース | URL | 使い方 |
|---|---|---|
| KataGo | https://github.com/lightvector/KataGo | ローカルで解析を自動実行し、各手の目数損失を記録 |
| KaTrain | https://github.com/sanderland/katrain | KataGo のGUI。人間レビュー用 |
| AI Sensei | https://ai-sensei.com | 必要に応じて照合 |

> 2026-10-22 時点で KataGo は未導入。`brew install katago` が依存ライブラリ libzip のダウンロード失敗（libzip.org への接続リセット）で止まっている。

## 自動化

- 調査スクリプトは [`../scripts/research/`](../scripts/research/)。取得した手順の生データは [`raw/`](./raw/)。
- パイプラインは `status: verified` の yaml を持つ定石だけを動画化する。
- KataGo 解析は自動で `ai_check` 欄を埋める。A〜C の照合結果は自分がレビューして記入する（＝勉強の工程）。
