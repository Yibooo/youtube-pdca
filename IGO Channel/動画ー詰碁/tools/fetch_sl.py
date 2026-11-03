#!/usr/bin/env python3
"""Sensei's Library の詰碁ページを 1 秒に 1 回ずつ取得して JSONL に保存する。

使い方: python fetch_sl.py <出力.jsonl> <ページ名> [<ページ名> ...]
途中で止まっても、同じコマンドで続きから取得する。
各ページの本文・棋譜（SGF）の URL と、/Solution ページがあればその本文・棋譜の URL を保存する。
"""
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://senseis.xmp.net/"


def get(url):
    for wait in (1, 30, 120, 300):  # 通信が切れたら間を空けてやり直す
        time.sleep(wait)
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "curl/8"}), timeout=30).read().decode("latin-1")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return ""
            raise
        except urllib.error.URLError as e:
            print(f"retry {url}: {e}", file=sys.stderr)
    raise SystemExit(f"通信できません: {url}")


def parse(h):
    m = re.search(r'</h1>(.*?)(?:<hr|last edited by)', h, re.S) or re.search(r'<body.*?>(.*?)last edited by', h, re.S)
    body = m.group(1) if m else ""
    sgfs = re.findall(r'href="(diagrams/[^"]+\.sgf)"', body)
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S)
    # 図の位置が分かるように [SGF] を残す
    text = re.sub(r'<a[^>]*href="diagrams/[^"]+\.sgf"[^>]*>.*?</a>', " [SGF] ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return {"text": re.sub(r"\s+", " ", html.unescape(text)).strip(), "sgfs": sgfs}


def main(out, pages):
    done = set()
    if os.path.exists(out):  # 取得済みのページは飛ばす
        done = {json.loads(x)["page"] for x in open(out, encoding="utf-8")}
    with open(out, "a", encoding="utf-8") as f:
        for name in pages:
            if name in done:
                continue
            q = urllib.parse.quote(name, safe="/")
            h = get(BASE + "?" + q)
            if not h or "does not yet exist" in h:
                continue
            rec = {"page": name, **parse(h)}
            s = get(BASE + "?" + q + "/Solution")
            if s and "does not yet exist" not in s:
                rec["solution"] = parse(s)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
