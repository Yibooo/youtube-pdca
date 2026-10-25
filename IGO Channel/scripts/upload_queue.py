#!/usr/bin/env python3
"""まだアップしていない回を、順番に非公開でアップロードする。

使い方:
    python upload_queue.py ep15 ep16 ...   （videos/ のフォルダ名の先頭一致）

- build/upload.json がある回はアップ済みとして飛ばす。
- 1日の上限（uploadLimitExceeded）に当たったら、そこで止めて終了コード 2 を返す。
- すべて済んだら終了コード 0。
"""
import sys
from pathlib import Path

from googleapiclient.errors import HttpError, ResumableUploadError

import upload

VIDEOS = Path(__file__).resolve().parent.parent / "videos"


def main(prefixes):
    targets = sorted(d for d in VIDEOS.iterdir() if d.is_dir() and any(d.name.startswith(p) for p in prefixes))
    for d in targets:
        if (d / "build" / "upload.json").exists():
            print(f"{d.name}: skip (uploaded)")
            continue
        try:
            upload.main(d / "spec.json")
        except (HttpError, ResumableUploadError) as e:
            if "uploadLimitExceeded" in str(e):
                print(f"{d.name}: LIMIT REACHED")
                return 2
            raise
    print("ALL DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
