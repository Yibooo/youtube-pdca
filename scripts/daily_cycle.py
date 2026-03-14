#!/usr/bin/env python3
"""
日次PDCAオーケストレーター（ルールベース版）
launchd から毎日09:00に呼び出される。

フロー:
  [Phase 1] 48h経過動画のパフォーマンスチェック → 学習DB更新
  [Phase 2] ルールベース仮説生成（テーマ×タイトル形式×サムネ×フック）
  [Phase 3] 動画生成・アップロード（変数を変えて毎日実験）
  [Phase 4] 日次レポート生成 → data/daily_report.json
  [Phase 5] state.json + daily_report.json を GitHub にプッシュ
"""
import sys, json, os, traceback, subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

# ── ログセットアップ ──
import logging

LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
today_str = datetime.now().strftime("%Y%m%d")
log_file  = LOG_DIR / f"daily_{today_str}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(str(log_file), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


def _load_config() -> dict:
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def _push_to_github(files: list):
    """指定ファイルを GitHub にプッシュする。"""
    today = datetime.now().strftime("%Y-%m-%d")
    cmds = [
        ["git", "add"] + files,
        ["git", "commit", "--allow-empty", "-m", f"[auto] PDCA日次結果 {today}"],
        ["git", "push", "origin", "main"],
    ]
    for cmd in cmds:
        r = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True, timeout=60)
        if r.returncode != 0 and "nothing to commit" not in r.stdout + r.stderr:
            logger.warning(f"⚠️  git {cmd[1]} エラー: {r.stderr.strip()[:200]}")
            return False
    logger.info("✅ GitHub プッシュ完了（Mission Control で確認可能）")
    return True


def _cleanup_output():
    """output/ の古いファイルを削除（7日超）"""
    import shutil, time
    cutoff = time.time() - 7 * 86400
    for subdir in ["audio", "images", "video"]:
        d = ROOT_DIR / "output" / subdir
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()


def _write_daily_report(check_results: dict, uploaded_videos: list,
                         config: dict, state: dict):
    """
    data/daily_report.json を生成する。
    Mission Control の /youtube-pdca ページが参照する。
    """
    from hypothesis_engine import get_insights, _load_perf_db

    db = _load_perf_db()
    insights = get_insights(db)

    total     = len(state.get("videos", []))
    success   = sum(1 for v in state["videos"] if v.get("status") == "success")
    pivoted   = sum(1 for v in state["videos"] if v.get("status") == "pivoted")
    pending   = sum(1 for v in state["videos"] if v.get("status") == "pending_check")

    checked_today = []
    for v in state["videos"]:
        if v.get("checked_at", "").startswith(datetime.now().strftime("%Y-%m-%d")):
            hyp = v.get("hypothesis", {})
            checked_today.append({
                "video_id":        v["video_id"],
                "title":           v.get("title", ""),
                "views_48h":       v.get("views_48h"),
                "status":          v.get("status"),
                "title_formula":   hyp.get("title_formula", "unknown"),
                "thumbnail_style": hyp.get("thumbnail_style", "unknown"),
                "hook_style":      hyp.get("hook_style", "unknown"),
            })

    report = {
        "date":             datetime.now().strftime("%Y-%m-%d"),
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "today_uploaded":   uploaded_videos,
        "checked_today":    checked_today,
        "check_summary":    check_results,
        "channel_stats": {
            "total_videos":   total,
            "success_count":  success,
            "pivot_count":    pivoted,
            "pending_count":  pending,
            "overall_avg_views": (
                sum(v.get("views_48h") or 0 for v in state["videos"] if v.get("views_48h") is not None)
                / max(success + pivoted, 1)
            ),
        },
        "performance_insights": insights,
        "performance_db_summary": {
            section: {
                k: {"trials": v.get("trials", 0), "avg_views": round(v.get("avg_views", 0), 1), "score": round(v.get("score", 0.5), 3)}
                for k, v in db.get(section, {}).items()
            }
            for section in ["title_formulas", "thumbnail_styles", "hook_styles"]
        },
        "next_run": "tomorrow 09:00 JST",
    }

    report_path = ROOT_DIR / "data" / "daily_report.json"
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ 日次レポート生成: {report_path.name}")
    return report


def generate_and_upload_one(hypothesis: dict, config: dict) -> dict | None:
    """
    1本の動画を生成・アップロードし、アップロード済みエントリを返す。
    """
    from generate_script  import generate as gen_script
    from generate_slides  import generate as gen_slides
    from generate_tts     import generate as gen_tts
    from build_video      import build as build_video
    from upload_youtube   import upload as upload_yt
    from check_analytics  import add_video_to_state

    theme_id        = hypothesis["theme_id"]
    title           = hypothesis.get("title")
    hook_text       = hypothesis.get("hook_text")
    hook_style      = hypothesis.get("hook_style")
    thumbnail_style = hypothesis.get("thumbnail_style", "dark_navy")

    logger.info(f"🎬 動画生成: [{hypothesis.get('title_formula')}×{thumbnail_style}×{hook_style}]")
    logger.info(f"   タイトル: {title}")

    try:
        script      = gen_script(theme_id, title=title, hook_text=hook_text, hook_style=hook_style)
        image_paths = gen_slides(script["slides"], theme_id, thumbnail_style=thumbnail_style)
        audio_path, durations = gen_tts(script["slides"], theme_id)
        video_path  = build_video(image_paths, audio_path, durations, theme_id)
        video_id    = upload_yt(video_path, hypothesis, script, durations)

        upload_time = datetime.now(timezone.utc).isoformat()
        add_video_to_state(video_id, script["title"], hypothesis, upload_time)

        logger.info(f"✅ 完了: https://www.youtube.com/watch?v={video_id}")
        return {
            "video_id":        video_id,
            "title":           script["title"],
            "theme_id":        theme_id,
            "title_formula":   hypothesis.get("title_formula"),
            "thumbnail_style": thumbnail_style,
            "hook_style":      hook_style,
            "upload_time":     upload_time,
        }

    except Exception as e:
        logger.error(f"❌ 動画生成エラー: {e}")
        logger.error(traceback.format_exc())
        return None


def run():
    logger.info("\n" + "=" * 60)
    logger.info(f"🚀 PDCA日次サイクル開始: {datetime.now().isoformat()}")
    logger.info("=" * 60)

    config = _load_config()
    pdca_cfg   = config.get("pdca", {})
    max_videos = pdca_cfg.get("max_videos_per_day", 2)

    # credentials.json 確認
    creds_path = ROOT_DIR / config["youtube"]["credentials_file"]
    if not creds_path.exists():
        logger.error(f"❌ credentials.json が見つかりません: {creds_path}")
        sys.exit(1)

    # ── Phase 1: パフォーマンスチェック ──
    logger.info("\n[Phase 1] 48h視聴数チェック + パフォーマンスDB更新")
    try:
        from check_analytics import check_and_update, load_state
        check_results = check_and_update()
        state = load_state()
    except Exception as e:
        logger.warning(f"⚠️ チェックエラー（続行）: {e}")
        check_results = {"checked": 0, "success": 0, "pivoted": 0}
        from check_analytics import load_state
        state = load_state()

    # ── Phase 2 & 3: 仮説生成 → 動画生成 ──
    logger.info(f"\n[Phase 2+3] 仮説生成 → 動画生成（最大{max_videos}本）")
    from hypothesis_engine import generate_hypothesis

    uploaded_videos = []
    for i in range(max_videos):
        logger.info(f"\n--- 動画 {i+1}/{max_videos} ---")
        state = load_state()  # 最新状態を毎回読み込む
        hypothesis = generate_hypothesis(config, state)
        result = generate_and_upload_one(hypothesis, config)
        if result:
            uploaded_videos.append(result)
            state = load_state()  # アップロード後に更新
        else:
            logger.warning("   ⚠️ スキップ")

    # ── Phase 4: 日次レポート生成 ──
    logger.info("\n[Phase 4] 日次レポート生成")
    state = load_state()
    _write_daily_report(check_results, uploaded_videos, config, state)

    # ── Phase 5: GitHub プッシュ ──
    logger.info("\n[Phase 5] GitHub プッシュ")
    _cleanup_output()
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    from check_analytics import save_state
    save_state(state)

    _push_to_github(["state.json", "data/daily_report.json", "data/performance_db.json"])

    logger.info(f"\n✅ 完了: {len(uploaded_videos)}/{max_videos}本アップロード")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
