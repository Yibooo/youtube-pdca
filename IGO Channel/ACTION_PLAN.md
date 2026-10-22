# アクションプラン

## Phase 0: 準備（1週目）

- [x] アップロード先チャンネルを決定：@FIRE-channel-yb を転用（2026-10-22）
- [ ] YouTube Studio でチャンネル名・説明・アイコン・ハンドルを囲碁向けに変更（本人が操作）
- [x] 旧「マネー研究所」の launchd 自動投稿を停止（2026-10-22。plist は `~/Library/LaunchAgents/com.youtube-pdca.plist.disabled` に退避）
- [x] KataGo を導入（2026-10-22。brew 版は macOS 14 の Swift で Metal ビルドが失敗するため、CPU/Eigen 版をソースからビルド。`quick_exit` を `_Exit` に置換する必要あり）。`scripts/katago_eval.py` で目数損失を計測
- [x] 定石書の代わりに日本語Webソース（GJ / IB / PN）を選定 → [sources/SOURCES.md](./sources/SOURCES.md)
- [x] Playlist 1 の定石を整理・照合 → [joseki/PLAYLIST1_hoshi_kogeima_kakari.md](./joseki/PLAYLIST1_hoshi_kogeima_kakari.md)（レビュー待ち）

## Phase 1: パイプライン構築（2〜3週目）

`2026_March/scripts` を `IGO Channel/scripts` に移植し、囲碁用に作り替える。

| 新モジュール | 元にするもの | 役割 |
|---|---|---|
| `sgf_loader.py` | 新規 | SGF読み込み（sgfmill）。基本形・変化・悪手の分岐を取り出す |
| `verify_joseki.py` | 新規 | yaml の検証ルール（3ソース・2カテゴリ・D必須）をチェック、KataGo解析で `ai_check` を自動記入 |
| `render_board.py` | generate_slides.py | 木目碁盤・石・手順番号・矢印を描画。1手ずつのフレーム生成 |
| `generate_script.py` | 同名 | SGF＋検証メモからナレーション台本を生成。**LLMには手順を渡すだけで、新しい手を作らせない** |
| `generate_thumbnail.py` | generate_slides.py | 問題局面＋問いかけ文字。A/B 2案 |
| `generate_tts.py` / `build_video.py` | 同名 | VOICEVOX ＋ ffmpeg（そのまま流用） |
| `upload_youtube.py` | 同名 | プレイリスト追加・カテゴリ「教育(27)」・概要欄に検証ソースを自動記載 |
| `daily_cycle.py` | 同名 | 次の verified 定石を1本取り出して生成→投稿。PDCAは再生数＋CTR＋視聴維持率で評価 |

## Phase 2: パイロット（4週目）

- [ ] Playlist 1-A の #1〜#3 を手動レビュー付きで生成し、限定公開で品質確認
- [ ] 盤面・読み上げ（囲碁用語の読み: 三々=さんさん、一間=いっけん 等）の辞書をVOICEVOXに登録
- [ ] 問題なければ公開。Shorts も同時投稿

## Phase 3: 定常運用（2ヶ月目〜）

- 週3〜4本（長尺）＋ 各Shorts。1本あたりの自分の作業はソース照合レビュー 20〜30分を目安
- 毎週: タイトル型・サムネ型ごとの CTR を比較し、勝ち型の比率を上げる（2026_March の pdca_engine を流用）
- Playlist 1 完了 → まとめ回 → Playlist 2（ダイレクト三々）→ 3 → 4 → 小目

## KPI（目安）

| 時期 | 本数（長尺） | 登録者 | 総再生時間 |
|---|---|---|---|
| 1ヶ月目 | 10 | 100 | 200h |
| 3ヶ月目 | 40 | 1,000 | 2,000h |
| 6ヶ月目 | 80 | 3,000 | 4,000h（収益化申請） |

## リスクと対策

| リスク | 対策 |
|---|---|
| 間違った定石を公開 | 3ソース検証＋KataGo必須＋人間レビュー。コメントで指摘があれば yaml に記録し訂正動画 |
| AI量産コンテンツとして収益化不可 | 独自の「間違いポイント」分析、検証記録の公開、投稿頻度を抑える |
| 著作権 | 書籍の図・文章、他チャンネルのサムネ・台本は流用しない。手順（棋譜）の照合のみ |
