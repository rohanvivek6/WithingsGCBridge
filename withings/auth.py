import datetime
import json
import logging
import queue
import threading
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Any

import requests
from flask import Flask, request

_TIMEOUT = (10, 30)  # (connect seconds, read seconds)
from werkzeug.datastructures import MultiDict

logger = logging.getLogger("wt_gc_bridge")

app = Flask(__name__)
code_queue: queue.Queue[MultiDict] = queue.Queue()


@app.route("/")
def get_token() -> str:
    code_queue.put(request.args)
    return "<p>Success!</p>"


def start_callback_server(port: int) -> None:
    threading.Thread(
        target=lambda: app.run(debug=False, host="0.0.0.0", port=port),
        daemon=True,
    ).start()


class WithingsAuth:
    def __init__(self, client_id: str, client_secret: str, callback_uri: str, tokenstore: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_uri = callback_uri
        self.parsed_uri = urllib.parse.urlparse(callback_uri)
        self.tokenstore = tokenstore

    def init(self) -> str:
        """Return a valid access token, running the OAuth flow if needed."""
        token_path = Path(self.tokenstore) / "withings.json"
        if not token_path.exists():
            logger.info("Running Withings authorization flow")
            auth_code = self.obtain_authorization_code()
            access_token, refresh_token = self.request_access_token(auth_code)
        else:
            with token_path.open() as f:
                tokens = json.load(f)
            access_token, refresh_token = self.request_refresh(tokens["refresh_token"])

        with token_path.open("w") as f:
            json.dump({"refresh_token": refresh_token}, f)

        return access_token

    def obtain_authorization_code(self) -> Any:
        scopes = ["user.metrics"]
        redirect_uri = urllib.parse.urlunparse(self.parsed_uri)
        state = str(hash(datetime.datetime.now()))
        authorize_url = (
            f"https://account.withings.com/oauth2_user/authorize2"
            f"?response_type=code&client_id={self.client_id}"
            f"&scope={','.join(scopes)}&redirect_uri={redirect_uri}&state={state}"
        )
        logger.info(f"Redirecting to {authorize_url}")
        webbrowser.open(authorize_url)
        logger.debug("Waiting for authorization code")
        result = code_queue.get(timeout=60)
        assert result.get("state") == state, "State does not match"
        logger.debug("Got valid auth code")
        auth_code = result.get("code")
        assert auth_code is not None, "No auth code in response"
        return auth_code

    def request_access_token(self, auth_code: str) -> tuple[str, str]:
        payload = {
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": auth_code,
            "redirect_uri": urllib.parse.urlunparse(self.parsed_uri),
        }
        logger.debug("Requesting access token...")
        result = requests.get(
            "https://wbsapi.withings.net/v2/oauth2", params=payload, timeout=_TIMEOUT
        ).json()["body"]
        access_token = result["access_token"]
        refresh_token = result["refresh_token"]
        logger.debug("Got access token.")
        return access_token, refresh_token

    def request_refresh(self, refresh_token: str) -> tuple[str, str]:
        logger.debug("Refreshing token...")
        payload = {
            "action": "requesttoken",
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        result = requests.get(
            "https://wbsapi.withings.net/v2/oauth2", params=payload, timeout=_TIMEOUT
        ).json()["body"]
        access_token = result["access_token"]
        refresh_token = result["refresh_token"]
        logger.debug("Got new access token.")
        return access_token, refresh_token
