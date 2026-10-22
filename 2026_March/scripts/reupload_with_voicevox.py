#!/usr/bin/env python3
"""
VOICEVOX音声で既存テーマを再生成・再アップロードするスクリプト。
使用例: python scripts/reupload_with_voicevox.py nisa_basics nisa_mistakes
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

import json, logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def reupload(theme_id: str):
    """指定テーマを再生成してYouTubeにアップロードする。"""
    from generate_script  import generate as gen_script
    from generate_slides  import generate as gen_slides
    from generate_tts     import generate as gen_tts
    from build_video      import build as build_video
    from upload_youtube   import upload as upload_yt
    from check_analytics  import load_state, save_state

    config = json.loads((ROOT_DIR / "config.json").read_text(encoding="utf-8"))

    # テーマ情報を config から取得
    themes = {t["id"]: t for t in config["themes"]}
    if theme_id not in themes:
        logger.error(f"❌ テーマが見つかりません: {theme_id}")
        logger.error(f"   利用可能: {list(themes.keys())}")
        return

    theme = themes[theme_id]
    hypothesis = {
        "theme_id":   theme["id"],
        "theme_name": theme["name"],
        "target":     theme["target"],
        "need":       theme["need"],
        "keyword":    theme["keyword"],
        "tags":       theme.get("tags", []),
    }

    logger.info(f"🔄 再生成・再アップロード開始: {theme['name']}")

    # Step 1: スクリプト生成
    logger.info("📝 スクリプト生成...")
    script = gen_script(theme_id)

    # Step 2: スライド画像生成
    logger.info("🖼  スライド画像生成...")
    image_paths = gen_slides(script["slides"], theme_id)

    # Step 3: VOICEVOX TTS音声生成
    logger.info("🎤 VOICEVOX TTS音声生成...")
    audio_path, durations = gen_tts(script["slides"], theme_id)

    # Step 4: 動画生成
    logger.info("🎬 動画生成（FFmpeg）...")
    video_path = build_video(image_paths, audio_path, durations, theme_id)

    # Step 5: YouTubeアップロード
    logger.info("📤 YouTubeアップロード...")
    video_id = upload_yt(video_path, hypothesis, script, durations)

    # Step 6: state.jsonに記録（新エントリとして追加）
    state = load_state()
    upload_time = datetime.now(timezone.utc).isoformat()
    state["videos"].append({
        "video_id":    video_id,
        "title":       script["title"],
        "hypothesis":  hypothesis,
        "upload_time": upload_time,
        "views_48h":   None,
        "status":      "pending_check",
        "tts_engine":  "voicevox",
        "note":        "reuploaded with VOICEVOX",
    })
    save_state(state)

    logger.info(f"✅ 完了: https://www.youtube.com/watch?v={video_id}")
    return video_id


def main():
    themes = sys.argv[1:] if len(sys.argv) > 1 else ["nisa_basics", "nisa_mistakes"]

    logger.info("=" * 60)
    logger.info("🚀 VOICEVOX再アップロード開始")
    logger.info(f"   対象テーマ: {themes}")
    logger.info("=" * 60)

    for theme_id in themes:
        logger.info(f"\n--- {theme_id} ---")
        video_id = reupload(theme_id)
        if video_id:
            logger.info(f"   ✅ アップロード済み: {video_id}")

    logger.info("\n✅ 全テーマの再アップロード完了")


if __name__ == "__main__":
    main()
