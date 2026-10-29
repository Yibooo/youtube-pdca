#!/usr/bin/env python3
"""YouTube の認証をやり直して token.json を作り直す（ブラウザで Google にログインして許可する）。

テスト中の Google API プロジェクトでは、ログイン情報が7日ほどで切れるため、そのときに実行する。
"""
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

ROOT = Path(__file__).resolve().parent.parent
flow = InstalledAppFlow.from_client_secrets_file(str(ROOT / "credentials.json"), ["https://www.googleapis.com/auth/youtube"])
creds = flow.run_local_server(port=8765, open_browser=True, prompt="consent",
                              authorization_prompt_message="ブラウザで Google にログインして許可してください: {url}")
(ROOT / "token.json").write_text(creds.to_json())
print("TOKEN_SAVED", flush=True)
