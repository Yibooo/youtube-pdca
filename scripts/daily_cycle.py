#!/usr/bin/env python3
"""
日次オーケストレーター（メインエントリーポイント）
launchd から毎日09:00に呼び出される。

フロー:
  [Phase 1] 48h経過動画のパフォーマンスチェック → PIVOT判定
  [Phase 2] 新規動画を max_videos_per_day 本生成・アップロード
  [Phase 3] ログ記録・サマリー表示
"""
import sys, json, os, traceback
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

# ── ログセットアップ ──
import logging

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / f"daily_{datetime.now().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def _load_config():
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def _cleanup_output():
    """output/ ディレクトリの古いファイルを削除（ディスク節約）"""
    import shutil, time
    KEEP_DAYS = 7
    cutoff = time.time() - KEEP_DAYS * 86400
    for subdir in ["audio", "images", "video"]:
        d = ROOT_DIR / "output" / subdir
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()


def generate_and_upload_one(hypothesis: dict) -> bool:
    """
    1本の動画を生成してYouTubeにアップロードする。
    Returns:
        bool: 成功したかどうか
    """
    from generate_script  import generate as gen_script
    from generate_slides  import generate as gen_slides
    from generate_tts     import generate as gen_tts
    from build_video      import build as build_video
    from upload_youtube   import upload as upload_yt
    from check_analytics  import add_video_to_state

    theme_id = hypothesis["theme_id"]
    logger.info(f"🎬 動画生成開始: {hypothesis['theme_name']}")
    logger.info(f"   ターゲット: {hypothesis['target']}")
    logger.info(f"   ニーズ: {hypothesis['need']}")

    try:
        # Step 1: スクリプト生成
        logger.info("📝 スクリプト生成...")
        script = gen_script(theme_id)

        # Step 2: スライド画像生成
        logger.info("🖼  スライド画像生成...")
        image_paths = gen_slides(script["slides"], theme_id)

        # Step 3: TTS音声生成
        logger.info("🎤 TTS音声生成...")
        audio_path, durations = gen_tts(script["slides"], theme_id)

        # Step 4: 動画生成
        logger.info("🎬 動画生成（FFmpeg）...")
        video_path = build_video(image_paths, audio_path, durations, theme_id)

        # Step 5: YouTubeアップロード
        logger.info("📤 YouTubeアップロード...")
        video_id = upload_yt(video_path, hypothesis, script, durations)

        # Step 6: state.jsonに記録
        upload_time = datetime.now(timezone.utc).isoformat()
        add_video_to_state(video_id, script["title"], hypothesis, upload_time)

        logger.info(f"✅ 完了: https://www.youtube.com/watch?v={video_id}")
        return True

    except FileNotFoundError as e:
        logger.error(f"❌ ファイルエラー: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 予期しないエラー: {e}")
        logger.error(traceback.format_exc())
        return False


def run():
    """
    1日のPDCAサイクルを実行する。
    """
    logger.info("\n" + "="*60)
    logger.info(f"🚀 PDCA日次サイクル開始: {datetime.now().isoformat()}")
    logger.info("="*60)

    config = _load_config()
    pdca_cfg = config.get("pdca", {})
    max_videos = pdca_cfg.get("max_videos_per_day", 2)

    # ── Phase 1: パフォーマンスチェック ──
    logger.info("\n[Phase 1] パフォーマンスチェック")
    try:
        from pdca_engine import run_check_phase, print_summary
        from check_analytics import load_state
        check_results = run_check_phase()
    except Exception as e:
        logger.warning(f"⚠️  チェックフェーズでエラー（続行します）: {e}")
        check_results = {"checked": 0, "success": 0, "pivoted": 0}

    # ── Phase 2: 新規動画生成・アップロード ──
    logger.info(f"\n[Phase 2] 新規動画生成（最大{max_videos}本）")

    # credentials.json の存在確認
    creds_path = ROOT_DIR / config["youtube"]["credentials_file"]
    if not creds_path.exists():
        logger.error(
            f"❌ credentials.json が見つかりません: {creds_path}\n"
            "   Google Cloud Console からダウンロードして配置してください。\n"
            "   → https://console.cloud.google.com/apis/credentials"
        )
        sys.exit(1)

    from pdca_engine import get_next_hypotheses
    hypotheses = get_next_hypotheses(n=max_videos)

    n_uploaded = 0
    for i, hyp in enumerate(hypotheses, 1):
        logger.info(f"\n--- 動画 {i}/{max_videos}: {hyp['theme_name']} ---")
        ok = generate_and_upload_one(hyp)
        if ok:
            n_uploaded += 1
        else:
            logger.warning(f"   ⚠️  スキップ（エラー発生）")

    # ── Phase 3: ログ・サマリー ──
    logger.info(f"\n[Phase 3] サイクル完了")

    try:
        from pdca_engine import log_cycle_result, print_summary
        from check_analytics import load_state
        log_cycle_result(check_results, n_uploaded)
        print_summary(load_state())
    except Exception as e:
        logger.warning(f"⚠️  ログ記録エラー: {e}")

    # 古い出力ファイルを削除
    _cleanup_output()

    logger.info(f"\n✅ 本日のサイクル完了: {n_uploaded}/{max_videos}本アップロード")
    logger.info("="*60)


if __name__ == "__main__":
    run()
