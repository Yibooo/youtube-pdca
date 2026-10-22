#!/usr/bin/env python3
"""
ルールベースPDCAエンジン（API不要版）

毎回「テーマ × タイトル形式 × サムネスタイル × フックスタイル」の
組み合わせを学習データに基づいて選び、仮説を生成する。

選択ロジック:
- スコア 0.0〜1.0（試行なし=0.5）を重みにしてソフトマックスで確率抽出
- 探索(exploration)と活用(exploitation)のバランスをTemperatureで調整
- 少ない試行回数は探索ボーナスが加算される（UCB的アプローチ）
"""
import json, math, random
from pathlib import Path
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent.parent
PERF_DB  = ROOT_DIR / "data" / "performance_db.json"

# ── タイトル形式 ──
# {n}=3or5, {kw}=keyword, {name}=theme_name, {target}=target, {need}=need
TITLE_FORMULAS = {
    "listicle": [
        "{name}で絶対やってはいけない{n}つのこと",
        "{kw}で{need}する人の特徴{n}選",
        "知らないと損する！{name}の{n}つのポイント",
    ],
    "question": [
        "{kw}って本当に効果があるの？正直に答えます",
        "{name}は本当に{target}に必要？メリット・デメリットを解説",
        "{kw}を始めるべき？やめるべき？徹底検証",
    ],
    "reversal": [
        "{kw}の常識は間違い！本当に{need}する方法",
        "みんなが{kw}で失敗する理由【正しいやり方教えます】",
        "{name}でよくある{n}つの誤解【これが正解です】",
    ],
    "urgency": [
        "今すぐ{kw}を始めないと{n}年後に後悔する理由",
        "{kw}を後回しにする人が損する{n}つのこと",
        "2026年に{kw}をやらないリスク【知らないと危険】",
    ],
    "secret": [
        "プロが教えない{kw}の活用法【{target}向け】",
        "FPも言わない{name}の裏技{n}選",
        "{target}だけが知っている{kw}の正しい使い方",
    ],
    "steps": [
        "{name}を{n}ステップで完全マスター【初心者ガイド】",
        "{kw}を始めるための{n}つの手順【完全解説】",
        "ゼロから{n}ヶ月で{name}を実現する具体的手順",
    ],
    "target": [
        "{target}必見！{name}で{need}するための完全ガイド",
        "{target}が{kw}で月{n}万円を増やす方法",
        "{target}向け：{kw}で{need}する{n}つの戦略",
    ],
}

# ── サムネスタイル（generate_slides.pyで使用） ──
THUMBNAIL_STYLES = [
    "dark_navy",     # 現行（ダークネイビー+ゴールド）
    "bright_red",    # 赤背景+白テキスト（緊急感・目立つ）
    "bright_yellow", # 黄背景+黒テキスト（注目度MAX）
    "gradient_blue", # 青グラデーション（プロフェッショナル）
    "split_dark",    # 左:大数字/アイコン 右:テキスト
    "minimal_white", # 白背景+黒太字（清潔感）
]

# ── フックスタイル（generate_script.pyで使用） ──
HOOK_STYLES = ["problem", "number", "result", "reversal", "question"]

# ── フック冒頭テンプレート（スライド1の narration 先頭に挿入） ──
HOOK_TEMPLATES = {
    "problem":  "今日は「{name}」について解説します。{need}で困っている方、必見です。",
    "number":   "実は9割の{target}が知らない、{name}の重要なポイントがあります。",
    "result":   "この動画を見ると、{need}できるようになります。{name}の全てを解説します。",
    "reversal": "{kw}についての常識、実は間違っているかもしれません。本当の答えをお伝えします。",
    "question": "あなたは{name}について正しく理解できていますか？今日は徹底的に解説します。",
}

NUMBERS = [3, 5, 7]


def _load_perf_db() -> dict:
    if PERF_DB.exists():
        with open(PERF_DB, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_perf_db(db: dict):
    PERF_DB.parent.mkdir(exist_ok=True)
    with open(PERF_DB, "w", encoding="utf-8") as f:
        db["last_updated"] = datetime.now(timezone.utc).isoformat()
        json.dump(db, f, ensure_ascii=False, indent=2)


def _softmax_choice(options_scores: dict, temperature: float = 0.8) -> str:
    """
    スコアをソフトマックスで確率に変換してランダム選択。
    temperature が高いほど均等選択（探索重視）。
    """
    items = list(options_scores.items())
    weights = [math.exp(s / temperature) for _, s in items]
    total = sum(weights)
    r = random.random() * total
    cumsum = 0.0
    for (k, _), w in zip(items, weights):
        cumsum += w
        if r <= cumsum:
            return k
    return items[-1][0]


def _ucb_score(record: dict, total_trials: int, exploration: float = 1.0) -> float:
    """UCB1スコア: avg_views/50 + exploration * sqrt(ln(total+1) / (trials+1))"""
    base = min(record.get("avg_views", 0) / 50.0, 1.0)
    n = record.get("trials", 0)
    ucb = exploration * math.sqrt(math.log(total_trials + 1) / (n + 1))
    return min(base + ucb, 1.5)


def _select_formula(db: dict) -> str:
    formulas = db.get("title_formulas", {})
    total = sum(r.get("trials", 0) for r in formulas.values())
    scores = {k: _ucb_score(v, total) for k, v in formulas.items()}
    return _softmax_choice(scores)


def _select_thumbnail(db: dict) -> str:
    thumbs = db.get("thumbnail_styles", {})
    total = sum(r.get("trials", 0) for r in thumbs.values())
    scores = {k: _ucb_score(v, total) for k, v in thumbs.items()}
    return _softmax_choice(scores)


def _select_hook(db: dict) -> str:
    hooks = db.get("hook_styles", {})
    total = sum(r.get("trials", 0) for r in hooks.values())
    scores = {k: _ucb_score(v, total) for k, v in hooks.items()}
    return _softmax_choice(scores)


def _select_theme(config: dict, state: dict, db: dict) -> dict:
    all_themes = config["themes"]
    used_today = _get_todays_themes(state)
    themes_db = db.get("themes", {})
    total = sum(r.get("trials", 0) for r in themes_db.values()) if themes_db else 0

    candidates = [t for t in all_themes if t["id"] not in used_today]
    if not candidates:
        candidates = all_themes  # 全て試した場合はリセット

    scores = {}
    for t in candidates:
        rec = themes_db.get(t["id"], {"trials": 0, "avg_views": 0})
        scores[t["id"]] = _ucb_score(rec, total)

    chosen_id = _softmax_choice(scores)
    return next(t for t in all_themes if t["id"] == chosen_id)


def _get_todays_themes(state: dict) -> list:
    """今日すでにアップロードしたテーマIDのリスト"""
    from datetime import date
    today = date.today().isoformat()
    result = []
    for v in state.get("videos", []):
        ut = v.get("upload_time", "")
        if ut.startswith(today):
            result.append(v.get("hypothesis", {}).get("theme_id", ""))
    return result


def _build_title(theme: dict, formula: str) -> str:
    n = random.choice(NUMBERS)
    templates = TITLE_FORMULAS.get(formula, TITLE_FORMULAS["listicle"])
    tpl = random.choice(templates)
    return tpl.format(
        n=n,
        kw=theme["keyword"],
        name=theme["name"],
        target=theme["target"],
        need=theme["need"],
    )


def _build_hook_text(theme: dict, hook_style: str) -> str:
    tpl = HOOK_TEMPLATES.get(hook_style, HOOK_TEMPLATES["problem"])
    return tpl.format(
        name=theme["name"],
        kw=theme["keyword"],
        target=theme["target"],
        need=theme["need"],
    )


def generate_hypothesis(config: dict, state: dict) -> dict:
    """
    1本分の仮説（テーマ・タイトル・サムネスタイル・フック）を生成する。
    """
    db = _load_perf_db()

    theme          = _select_theme(config, state, db)
    title_formula  = _select_formula(db)
    thumbnail_style = _select_thumbnail(db)
    hook_style     = _select_hook(db)

    title     = _build_title(theme, title_formula)
    hook_text = _build_hook_text(theme, hook_style)

    hypothesis = {
        "theme_id":        theme["id"],
        "theme_name":      theme["name"],
        "target":          theme["target"],
        "need":            theme["need"],
        "keyword":         theme["keyword"],
        "tags":            theme["tags"],
        # PDCA変数（パフォーマンス学習に使用）
        "title":           title,
        "title_formula":   title_formula,
        "thumbnail_style": thumbnail_style,
        "hook_style":      hook_style,
        "hook_text":       hook_text,
    }

    print(f"📌 仮説生成:")
    print(f"   テーマ:    {theme['name']}")
    print(f"   タイトル:  {title} [{title_formula}]")
    print(f"   サムネ:    {thumbnail_style}")
    print(f"   フック:    {hook_style}")
    return hypothesis


def update_performance(video_entry: dict):
    """
    チェック済み動画のパフォーマンスをDBに記録する。
    check_analytics.py から呼ばれる。
    """
    views = video_entry.get("views_48h")
    hyp   = video_entry.get("hypothesis", {})
    if views is None or views < 0:
        return

    db = _load_perf_db()

    def _update(section: str, key: str):
        if not key:
            return
        rec = db.setdefault(section, {}).setdefault(key, {
            "trials": 0, "total_views": 0, "avg_views": 0, "score": 0.5
        })
        rec["trials"]      += 1
        rec["total_views"] = rec.get("total_views", 0) + views
        rec["avg_views"]   = rec["total_views"] / rec["trials"]
        rec["score"]       = min(rec["avg_views"] / 50.0, 1.0)

    _update("title_formulas",   hyp.get("title_formula"))
    _update("thumbnail_styles", hyp.get("thumbnail_style"))
    _update("hook_styles",      hyp.get("hook_style"))
    _update("themes",           hyp.get("theme_id"))

    _save_perf_db(db)
    print(f"📊 パフォーマンスDB更新: {hyp.get('theme_id')} → {views}再生")


def get_insights(db: dict = None) -> dict:
    """
    現在の学習状況から人間が読めるインサイトを返す。
    Mission Control の日次レポートに使用。
    """
    if db is None:
        db = _load_perf_db()

    def _best(section: str):
        items = db.get(section, {})
        if not items:
            return "データ不足"
        tried = {k: v for k, v in items.items() if v.get("trials", 0) > 0}
        if not tried:
            return "未試行"
        best = max(tried.items(), key=lambda x: x[1]["avg_views"])
        return f"{best[0]} (avg {best[1]['avg_views']:.1f}再生 / {best[1]['trials']}試行)"

    return {
        "best_title_formula":  _best("title_formulas"),
        "best_thumbnail":      _best("thumbnail_styles"),
        "best_hook":           _best("hook_styles"),
        "best_theme":          _best("themes"),
        "total_experiments":   sum(
            v.get("trials", 0)
            for section in ["title_formulas", "thumbnail_styles", "hook_styles"]
            for v in db.get(section, {}).values()
        ) // 3,  # 3変数なので除算
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(ROOT_DIR / "scripts"))
    from generate_hypothesis import load_config, load_state

    config = load_config()
    state  = load_state()
    hyp    = generate_hypothesis(config, state)
    print(json.dumps(hyp, ensure_ascii=False, indent=2))
