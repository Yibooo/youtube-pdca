#!/usr/bin/env python3
"""spec.json と build/ の動画・サムネを YouTube に「非公開」でアップロードする。

使い方:
    python upload.py ../episodes/ep01_fastretailing_fy2026/spec.json --auth-dir <credentials.json と token.json のあるフォルダ>

- 公開は YouTube Studio から手動で行う（このスクリプトは公開しない）。
- 認証は囲碁チャンネルと同じもの（同じチャンネルにアップロードする）。token が切れていたら、
  ブラウザで Google にログインして許可する画面が開く。
- アップロードしたら build/upload.json に動画 ID を書く。upload.json がある回はアップロードしない。
"""
import argparse
import json
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/yt-analytics.readonly"]
# アップロード先：@IGO-Channel-JP（後で IR 向けに改名予定）。違うチャンネルの認証ならアップロードしない
EXPECTED_CHANNEL_ID = "UCZO7fh-u3AJ_1NppOjCahpg"


def service(auth_dir):
    token = auth_dir / "token.json"
    creds = Credentials.from_authorized_user_file(str(token), SCOPES) if token.exists() else None
    try:
        if creds and not creds.valid:
            creds.refresh(Request())
    except RefreshError:
        creds = None
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(auth_dir / "credentials.json"), SCOPES)
        creds = flow.run_local_server(port=8765, open_browser=True, prompt="consent",
                                      authorization_prompt_message="ブラウザで Google にログインして許可してください: {url}")
    token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def main(spec_path, auth_dir):
    spec_path = Path(spec_path).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    out = spec_path.parent / "build"
    if (out / "upload.json").exists():
        raise SystemExit(f"アップロード済みです: {out / 'upload.json'}")
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
    if len(body["snippet"]["title"]) > 100:
        raise SystemExit("タイトルが100文字を超えています")
    yt = service(Path(auth_dir).resolve())
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
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--auth-dir", required=True)
    a = ap.parse_args()
    main(a.spec, a.auth_dir)
