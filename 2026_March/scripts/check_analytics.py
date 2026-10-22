#!/usr/bin/env python3
"""
YouTube アナリティクス確認モジュール
state.jsonを読み込み、投稿から48h経過した動画の
視聴回数を取得してステータスを更新する。
"""
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT_DIR = Path(__file__).parent.parent
STATE_FILE = ROOT_DIR / "state.json"


def _load_config():
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {
            "videos": [],
            "used_themes": [],
            "pivot_count": 0,
            "success_patterns": [],
            "last_run": None
        }
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _is_ready_to_check(video: dict, check_hours: int) -> bool:
    """投稿からcheck_hours時間以上経過していてpending_checkなら確認対象"""
    if video.get("status") != "pending_check":
        return False
    upload_time_str = video.get("upload_time")
    if not upload_time_str:
        return False
    try:
        # ISO形式をパース
        upload_time = datetime.fromisoformat(upload_time_str)
        # タイムゾーンがなければUTCとして扱う
        if upload_time.tzinfo is None:
            upload_time = upload_time.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        elapsed = (now - upload_time).total_seconds() / 3600
        return elapsed >= check_hours
    except Exception:
        return False


def check_and_update() -> dict:
    """
    48h経過した動画の視聴回数を取得し、state.jsonを更新する。
    Returns:
        dict: {
            "checked": int,      # チェックした動画数
            "success": int,      # 閾値以上の動画数
            "pivoted": int,      # PIVOT判定した動画数
        }
    """
    config = _load_config()
    pdca_cfg = config.get("pdca", {})
    threshold = pdca_cfg.get("pivot_threshold_views", 30)
    check_hours = pdca_cfg.get("check_hours_after_upload", 48)

    state = load_state()

    # upload_youtube モジュールからget_video_views を利用
    import sys
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from upload_youtube import get_video_views

    results = {"checked": 0, "success": 0, "pivoted": 0}

    for video in state["videos"]:
        if not _is_ready_to_check(video, check_hours):
            continue

        video_id = video.get("video_id")
        if not video_id:
            continue

        print(f"📊 視聴回数チェック: {video_id} ({video.get('hypothesis', {}).get('theme_name', '')})")

        views = get_video_views(video_id)
        video["views_48h"] = views
        video["checked_at"] = datetime.now(timezone.utc).isoformat()

        if views < 0:
            print(f"   ⚠️  取得失敗（APIエラー）")
            continue

        results["checked"] += 1

        if views >= threshold:
            video["status"] = "success"
            results["success"] += 1

            # 成功パターンとして記録
            pattern = {
                "theme_id": video.get("hypothesis", {}).get("theme_id"),
                "theme_name": video.get("hypothesis", {}).get("theme_name"),
                "tags": video.get("hypothesis", {}).get("tags", []),
                "views": views,
                "title": video.get("title", ""),
            }
            state["success_patterns"].append(pattern)
            print(f"   ✅ SUCCESS: {views}回（閾値{threshold}回以上）")
        else:
            video["status"] = "pivoted"
            state["pivot_count"] = state.get("pivot_count", 0) + 1
            results["pivoted"] += 1
            print(f"   🔄 PIVOT: {views}回（閾値{threshold}回未満）")

        # ── パフォーマンスDBに記録（ルールベースPDCA学習） ──
        try:
            from hypothesis_engine import update_performance
            update_performance(video)
        except Exception as e:
            print(f"   ⚠️ パフォーマンスDB更新スキップ: {e}")

    save_state(state)

    print(f"\n📈 チェック完了: {results['checked']}件")
    print(f"   ✅ 成功: {results['success']}件  🔄 PIVOT: {results['pivoted']}件")
    return results


def add_video_to_state(
    video_id: str,
    title: str,
    hypothesis: dict,
    upload_time: str = None
):
    """
    新規アップロード動画をstate.jsonに追加する。
    daily_cycle.pyから呼ばれる。
    """
    state = load_state()

    if upload_time is None:
        upload_time = datetime.now(timezone.utc).isoformat()

    # used_themesに追加（PIVOT選定に使用）
    theme_id = hypothesis.get("theme_id")
    if theme_id and theme_id not in state["used_themes"]:
        state["used_themes"].append(theme_id)

    video_entry = {
        "video_id": video_id,
        "upload_time": upload_time,
        "hypothesis": hypothesis,
        "title": title,
        "views_48h": None,
        "status": "pending_check",
        "checked_at": None,
    }
    state["videos"].append(video_entry)
    save_state(state)
    print(f"📝 state.json 更新: {video_id} を記録しました")


if __name__ == "__main__":
    results = check_and_update()
    print(json.dumps(results, ensure_ascii=False, indent=2))
