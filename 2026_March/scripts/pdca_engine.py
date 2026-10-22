#!/usr/bin/env python3
"""
PDCAエンジン
1日のPDCAサイクルを管理する。
- Step1: 48h経過動画のパフォーマンスチェック
- Step2: 仮説選定（PIVOTが必要か判断して次のテーマを決める）
- 成功パターンの学習・記録
"""
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent.parent


def _load_config():
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def _load_state():
    from check_analytics import load_state
    return load_state()


def run_check_phase() -> dict:
    """
    フェーズ1: 48h経過動画のパフォーマンスチェック。
    Returns:
        dict: チェック結果サマリー
    """
    print("\n" + "="*60)
    print("📊 [Phase 1] パフォーマンスチェック開始")
    print("="*60)

    from check_analytics import check_and_update
    results = check_and_update()
    return results


def get_next_hypotheses(n: int = 2) -> list:
    """
    フェーズ2: 次に投稿する仮説をn個生成する。
    PIVOT判定結果を考慮してテーマを選定する。
    Args:
        n: 生成する仮説数（= max_videos_per_day）
    Returns:
        list of hypothesis dicts
    """
    from generate_hypothesis import generate, load_state
    state = load_state()

    hypotheses = []
    # 同じ日に同じテーマが出ないよう、仮のused_themesを更新しながら生成
    tmp_state = json.loads(json.dumps(state))  # ディープコピー

    for i in range(n):
        h = generate(state=tmp_state)
        hypotheses.append(h)
        # 次のループで同テーマが出ないよう一時的に使用済みとして扱う
        if h["theme_id"] not in tmp_state["used_themes"]:
            tmp_state["used_themes"].append(h["theme_id"])

    return hypotheses


def log_cycle_result(results: dict, n_uploaded: int):
    """
    1日のサイクル結果をログに記録する。
    """
    log_dir = ROOT_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "daily.log"

    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": now,
        "check_results": results,
        "videos_uploaded": n_uploaded,
    }

    # ログファイルに追記
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"\n📝 ログ記録完了: {log_file}")


def print_summary(state: dict):
    """
    現在の運用状況サマリーを表示する。
    """
    videos = state.get("videos", [])
    total = len(videos)
    success = sum(1 for v in videos if v.get("status") == "success")
    pivoted = sum(1 for v in videos if v.get("status") == "pivoted")
    pending = sum(1 for v in videos if v.get("status") == "pending_check")

    print("\n" + "="*60)
    print("📈 運用状況サマリー")
    print("="*60)
    print(f"   総投稿数:      {total}本")
    print(f"   ✅ 成功:       {success}本")
    print(f"   🔄 PIVOT済み:  {pivoted}本")
    print(f"   ⏳ チェック待: {pending}本")
    print(f"   累計PIVOT数:   {state.get('pivot_count', 0)}回")
    print(f"   成功パターン:  {len(state.get('success_patterns', []))}件")

    if state.get("success_patterns"):
        print("\n🏆 成功テーマトップ3:")
        top = sorted(
            state["success_patterns"],
            key=lambda x: x.get("views", 0),
            reverse=True
        )[:3]
        for i, p in enumerate(top, 1):
            print(f"   {i}. {p.get('theme_name')} — {p.get('views')}回再生")
    print("="*60)


if __name__ == "__main__":
    # PDCAエンジン単体テスト
    import sys
    sys.path.insert(0, str(ROOT_DIR / "scripts"))

    results = run_check_phase()

    from check_analytics import load_state
    state = load_state()
    print_summary(state)

    print("\n次の仮説:")
    hypotheses = get_next_hypotheses(n=2)
    for i, h in enumerate(hypotheses, 1):
        print(f"   {i}. {h['theme_name']} (target: {h['target']})")
