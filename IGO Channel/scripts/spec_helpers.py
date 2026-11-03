"""台本（spec.json）を Python で書くための補助。"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "動画ー定石" / "videos"
DESC = "{intro}\n\n━━━━━━━━━━━━━━━━\n⏰ チャプター\n{{chapters}}\n━━━━━━━━━━━━━━━━\n\nこの動画はAIを使って制作しています（台本の作成支援・盤面の自動描画・音声合成）。\n音声：VOICEVOX:No.7\n\n{hashtags}"


def B(caption, moves, sub, say, **kw):
    d = {"caption": caption, "moves": moves, "sub": sub, "say": say}
    d.update(kw)
    return d


def spec(n, slug, series, sn, base, joseki_id, title, intro, hashtags, tags, beats, thumb):
    s = {"id": f"ep{n:02d}_{slug}", "joseki_id": joseki_id, "series": f"{series} #{sn}", "base": base,
         "voice": {"speaker": 30, "speed": 1.1},
         "youtube": {"title": f"【囲碁定石 {series} #{sn}】{title}", "description": DESC.format(intro=intro, hashtags=hashtags),
                     "tags": ["囲碁", "定石", "囲碁定石", "囲碁講座", "囲碁初心者", "Go", "Baduk", "Joseki"] + tags, "category_id": "27"},
         "beats": beats, "thumbnail": thumb}
    d = ROOT / s["id"]
    d.mkdir(parents=True, exist_ok=True)
    (d / "spec.json").write_text(json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", s["id"], len(beats))
