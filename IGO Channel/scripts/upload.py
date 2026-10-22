#!/usr/bin/env python3
"""spec.json と build/ の成果物を YouTube に「非公開」でアップロードする。

使い方:
    python upload.py ../videos/ep01_ikken_takabasami/spec.json

公開は YouTube Studio から手動で行う（このスクリプトは公開しない）。
認証: IGO Channel/credentials.json と token.json（どちらも .gitignore 済み）。
"""
import json
import sys
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/youtube"]
# アップロード先：囲碁好きの定石チャンネル（@IGO-Channel-JP）。違うチャンネルの認証ならアップロードしない
EXPECTED_CHANNEL_ID = "UCZO7fh-u3AJ_1NppOjCahpg"


def service():
    token = ROOT / "token.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def main(spec_path):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out = spec_path.parent / "build"
    meta = spec["youtube"]
    chapters = (out / "chapters.txt").read_text(encoding="utf-8").strip()
    body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"].replace("{chapters}", chapters),
            "tags": meta["tags"],
            "categoryId": meta["category_id"],
            "defaultLanguage": "ja",
            "defaultAudioLanguage": "ja",
        },
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
    }
    yt = service()
    ch = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
    if ch["id"] != EXPECTED_CHANNEL_ID:
        raise SystemExit(f"認証中のチャンネルが違います: {ch['snippet']['title']} ({ch['id']})")
    print(f"channel: {ch['snippet']['title']} ({ch['snippet'].get('customUrl')})")
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(out / "video.mp4"), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    print(f"uploaded: https://youtu.be/{vid}  (private)")
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(out / "thumbnail.png"))).execute()
        print("thumbnail: set")
    except Exception as e:  # 電話番号未認証のチャンネルではカスタムサムネが拒否される
        print(f"thumbnail: failed ({e})")
    (out / "upload.json").write_text(json.dumps({"video_id": vid, "privacy": "private"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
