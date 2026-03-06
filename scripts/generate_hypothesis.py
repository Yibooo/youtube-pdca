#!/usr/bin/env python3
"""
仮説生成モジュール
state.jsonの履歴を参照し、次に投稿するテーマと仮説を選定する。
PIVOTが必要な場合は未試行テーマを優先して選ぶ。
"""
import json
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent


def load_config():
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    state_path = ROOT_DIR / "state.json"
    if not state_path.exists():
        return {"videos": [], "used_themes": [], "pivot_count": 0,
                "success_patterns": [], "last_run": None}
    with open(state_path, encoding="utf-8") as f:
        return json.load(f)


def _select_theme(config, state):
    """
    テーマ選定ロジック:
    1. 成功パターン（views >= 閾値）があれば類似テーマを優先
    2. まだ一度も使っていないテーマを選ぶ
    3. 全テーマ使用済みなら最も古く使ったテーマを選ぶ
    """
    all_themes = config["themes"]
    used = state.get("used_themes", [])
    success_patterns = state.get("success_patterns", [])

    # 未使用テーマ
    unused = [t for t in all_themes if t["id"] not in used]
    if unused:
        # 成功パターンと同じキーワードを持つテーマを優先
        if success_patterns:
            successful_tags = set()
            for sp in success_patterns:
                successful_tags.update(sp.get("tags", []))
            scored = sorted(
                unused,
                key=lambda t: len(set(t["tags"]) & successful_tags),
                reverse=True
            )
            return scored[0]
        return unused[0]

    # 全テーマ使用済みの場合: もっとも長く未使用のテーマを選ぶ
    used_order = {tid: i for i, tid in enumerate(used)}
    return sorted(all_themes, key=lambda t: used_order.get(t["id"], -1))[0]


def generate(state=None):
    """
    仮説を生成して返す。
    Returns:
        dict: {
            "theme_id": str,
            "theme_name": str,
            "target": str,
            "need": str,
            "keyword": str,
            "tags": list
        }
    """
    config = load_config()
    if state is None:
        state = load_state()

    theme = _select_theme(config, state)

    hypothesis = {
        "theme_id": theme["id"],
        "theme_name": theme["name"],
        "target": theme["target"],
        "need": theme["need"],
        "keyword": theme["keyword"],
        "tags": theme["tags"]
    }

    print(f"📌 仮説決定:")
    print(f"   テーマ: {theme['name']}")
    print(f"   ターゲット: {theme['target']}")
    print(f"   ニーズ: {theme['need']}")

    return hypothesis


if __name__ == "__main__":
    h = generate()
    print(json.dumps(h, ensure_ascii=False, indent=2))
