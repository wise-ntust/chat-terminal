import json
import os
import time
import webbrowser
from datetime import datetime
from typing import Dict, Optional

import requests

from .config import config


def get_auth() -> Optional[Dict]:
    auth_data = config.get_auth()
    if auth_data:
        return auth_data.dict()
    return None


def start_oauth_flow():
    try:
        response = requests.get(f"{config.settings.server_url}/auth/login")
        data = response.json()

        if "client_id" in data:
            client_id = data["client_id"]
            auth_url = data.get("auth_url")
            if auth_url:
                webbrowser.open(auth_url)
            return client_id
        return None
    except Exception:
        return None


def wait_for_auth_completion(client_id: str):
    MAX_RETRIES = 30
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            response = requests.get(
                f"{config.settings.server_url}/auth/token/{client_id}"
            )
            data = response.json()

            if "status" in data and data["status"] == "pending":
                time.sleep(1)
                retry_count += 1
                continue

            if "user_id" in data:
                return data
            return None
        except Exception:
            time.sleep(1)
            retry_count += 1
            continue
    return None


def save_token(data: Dict) -> bool:
    return config.save_auth(data)


def login_flow() -> Dict:
    # Step 1: Start OAuth flow
    client_id = start_oauth_flow()
    if not client_id:
        return {"status": "failed", "message": "Failed to start OAuth flow"}

    # Step 2: Wait for authorization completion
    auth_data = wait_for_auth_completion(client_id)
    if not auth_data:
        return {
            "status": "failed",
            "message": "Failed to wait for authorization completion",
        }

    # Step 3: Save token
    save_token(auth_data)

    return {"status": "success", "message": "Login successful"}
