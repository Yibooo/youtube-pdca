# IGO Channel — AI自動生成の囲碁定石解説チャンネル

定石解説動画をAIで自動生成・自動投稿して収益化を目指しつつ、制作過程そのものを自分の定石勉強にするプロジェクト。

> 旧プロジェクト（資産形成チャンネル「マネー研究所」の自動投稿システム）は [`../2026_March/`](../2026_March/) にアーカイブ。
> 動画生成・TTS・アップロード・PDCAの仕組みはそこから流用する。

## ドキュメント

| ファイル | 内容 |
|---|---|
| [動画ー定石/EPISODES_1-50.md](./動画ー定石/EPISODES_1-50.md) | **動画リスト #1〜#50（作る順番・テーマ・問題ネタ・状態）** |
| [動画ー定石/VIDEO_TEMPLATE.md](./動画ー定石/VIDEO_TEMPLATE.md) | **動画テンプレート（問題→正解→不正解の手順と損失→まとめ）と台本・音声のルール** |
| [STRATEGY.md](./STRATEGY.md) | 方針・ベンチマーク分析（柳澤理志チャンネル）・タイトル/サムネ規則・収益化戦略 |
| [動画ー定石/CONTENT_ROADMAP.md](./動画ー定石/CONTENT_ROADMAP.md) | プレイリスト構成と動画リスト（星・小ケイマかかり → ダイレクト三々 → 一間かかり … → 小目） |
| [ACTION_PLAN.md](./ACTION_PLAN.md) | フェーズ別アクションプランとKPI |
| [動画ー定石/joseki/PLAYLIST1_hoshi_kogeima_kakari.md](./動画ー定石/joseki/PLAYLIST1_hoshi_kogeima_kakari.md) | **Playlist 1 の定石整理・検証表（レビュー待ち）** |
| [動画ー定石/sources/SOURCES.md](./動画ー定石/sources/SOURCES.md) | 信頼できる定石ソース一覧と「3ソース検証ルール」 |
| [動画ー定石/sources/verification_template.yaml](./動画ー定石/sources/verification_template.yaml) | 定石1本ごとの検証記録テンプレート |

## ディレクトリ構成

```
IGO Channel/
├── 動画ー定石/        # 定石の長尺動画（台本・検証表・ソース・調査ツール）
├── 動画ー詰碁/        # 詰碁の長尺動画（方針・問題集・検証ツール）
├── Shortsー定石/      # 定石の Shorts（台本・縦型レンダラー）
├── scripts/           # 共通ツール（描画、VOICEVOX、KataGo、アップロード、認証）
├── STRATEGY.md        # チャンネル全体の方針
└── ACTION_PLAN.md     # チャンネル全体のアクションプラン
```

## 基本原則

1. **SGFが唯一の正** — 台本・盤面アニメ・サムネはすべて検証済みSGFから生成。LLMに手順を「考えさせない」。
2. **3ソース検証なしに公開しない** — `sources/<joseki_id>.yaml` で `status: verified` になった定石だけがパイプラインに入る。
3. **自分の勉強にする** — 検証作業（ソース照合・AI評価の確認）は人間（自分）がレビューする工程として残す。
