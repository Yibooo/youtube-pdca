#!/usr/bin/env python3
"""
YouTube アップロードモジュール
既存 youtube-automation の 4_upload_youtube.py をベースに拡張。
スコープを youtube（フルアクセス）に変更し、統計取得も対応。
"""
import json, sys, os
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent.parent

# フルアクセスに変更（統計取得に youtube.readonly が必要）
SCOPES = ["https://www.googleapis.com/auth/youtube"]


def _load_config():
    with open(ROOT_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


def get_service():
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    config = _load_config()
    token_path = ROOT_DIR / config["youtube"]["token_file"]
    creds_path = ROOT_DIR / config["youtube"]["credentials_file"]
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"credentials.json が見つかりません: {creds_path}\n"
                    "Google Cloud Console からダウンロードして配置してください。"
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())
        print("✅ token.json 保存済み（次回から自動ログイン）")

    return build("youtube", "v3", credentials=creds)


def _build_chapters(slides_data: list, durations: list) -> str:
    """スライドデータから YouTube チャプター文字列を生成する。"""
    chapters = []
    t = 0
    for i, (slide, dur) in enumerate(zip(slides_data, durations)):
        mm, ss = divmod(int(t), 60)
        heading = slide.get("heading", f"パート{i+1}")
        chapters.append(f"{mm:02d}:{ss:02d} {heading}")
        t += dur
    return "\n".join(chapters)


def upload(
    video_path: str,
    hypothesis: dict,
    script_data: dict,
    durations: list = None
) -> str:
    """
    動画をYouTubeにアップロードする。
    Args:
        video_path: MP4ファイルのパス
        hypothesis: generate_hypothesis.pyが返す仮説dict
        script_data: generate_script.pyが返すスクリプトdict
        durations: 各スライドの尺リスト（チャプター生成用）
    Returns:
        str: YouTube動画ID
    """
    from googleapiclient.http import MediaFileUpload

    config = _load_config()
    yt_cfg = config["youtube"]
    ch_cfg = config["channel"]

    title = script_data["title"]
    slides = script_data.get("slides", [])

    # チャプター生成
    if durations:
        chapters = _build_chapters(slides, durations)
    else:
        chapters = ""

    description = ch_cfg["description_template"].format(
        title=title,
        description=script_data.get("description", ""),
        chapters=chapters,
        keyword=hypothesis.get("keyword", "資産形成")
    )

    # タグ：ベースタグ + テーマタグ
    tags = yt_cfg["base_tags"] + hypothesis.get("tags", [])
    tags = list(dict.fromkeys(tags))  # 重複除去

    print(f"📤 アップロード中...")
    print(f"   タイトル: {title}")

    yt = get_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": yt_cfg["category_id"],
        },
        "status": {
            "privacyStatus": yt_cfg["privacy_status"]
        }
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024
    )

    req = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"   進捗: {int(status.progress() * 100)}%", end="\r")

    video_id = resp["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\n✅ アップロード完了!")
    print(f"   URL: {url}")
    return video_id


def get_video_views(video_id: str) -> int:
    """
    動画の現在の視聴回数を取得する。
    Args:
        video_id: YouTube動画ID
    Returns:
        int: 視聴回数（取得失敗時は -1）
    """
    try:
        yt = get_service()
        resp = yt.videos().list(
            part="statistics",
            id=video_id
        ).execute()

        items = resp.get("items", [])
        if not items:
            return -1

        stats = items[0].get("statistics", {})
        return int(stats.get("viewCount", 0))
    except Exception as e:
        print(f"⚠️  視聴回数取得エラー: {e}")
        return -1


if __name__ == "__main__":
    # 視聴回数チェックのテスト
    if len(sys.argv) > 1:
        vid = sys.argv[1]
        views = get_video_views(vid)
        print(f"動画 {vid} の視聴回数: {views}")
