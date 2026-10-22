# YouTube PDCA 自動運用システム

資産形成・FIRE・投資テーマのYouTube動画を**完全自動**で生成・投稿し、再生データに基づいてPDCAを回し続けるシステム。

## 特徴

- **完全自動** — macOS launchd により毎日09:00に自動実行。人間の操作不要
- **PDCA自律実行** — 48h後の視聴回数を自動確認し、30回未満ならテーマをPIVOT
- **コスト$0** — YouTube API無料枠・macOS TTS・FFmpeg・Pillowのみ使用
- **資産形成テーマ** — 15種のテーマ（NISA・FIRE・iDeCo・高配当株など）を自動ローテーション

## システムフロー

```
毎日09:00（launchd）
  ↓
① 48h経過動画のパフォーマンスチェック
  → 視聴回数 ≥ 30回 → SUCCESS（成功パターン記録）
  → 視聴回数 < 30回 → PIVOT（テーマ変更）
  ↓
② 新規動画を2本生成・投稿
  仮説生成 → スクリプト生成 → スライド画像生成
  → TTS音声生成 → 動画結合 → YouTubeアップロード
```

## セットアップ（開発完了後）

```bash
# 1. 依存パッケージをインストール
pip install google-api-python-client google-auth-oauthlib pillow

# 2. YouTube API認証情報を配置
cp ~/Downloads/client_secret_*.json credentials.json

# 3. launchd に登録して自動化開始
./setup/setup_launchd.sh
```

## 詳細

→ [要件定義書.md](./要件定義書.md) を参照

## ステータス

🟡 **要件定義完了・開発開始前**
