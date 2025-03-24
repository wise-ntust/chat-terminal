import threading
import time
from datetime import datetime
from typing import Dict, List

import requests
from textual import events, log
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Input, Label, ListItem, ListView, RichLog

from .auth import get_auth
from .config import config


def format_message(message: Dict, user_id: str) -> str:
    content = message["content"]
    sent_at = datetime.strptime(message["sent_at"], "%Y-%m-%dT%H:%M:%S.%f").strftime(
        config.settings.time_format
    )
    color = "gray" if message["sender_id"] == user_id else "green"

    return f"[{sent_at}] [{color}]{content}[/{color}]"


def fetch_chatrooms(user_id: str) -> List[Dict]:
    auth = get_auth()
    if not auth:
        return []

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.get(
            f"{config.settings.server_url}/chat/chatrooms",
            params={"user_id": user_id},
            headers=headers,
        )
        if response.status_code == 200:
            return response.json().get("chatrooms", [])
        else:
            log.error(f"Failed to get chatrooms: {response.status_code}")
            return []
    except Exception as e:
        log.error(f"Failed to get chatrooms: {e}")
        return []


def fetch_messages(
    chatroom_id: str, user_id: str, limit: int = None, skip: int = 0
) -> List[Dict]:
    if limit is None:
        limit = config.settings.max_messages

    try:
        response = requests.get(
            f"{config.settings.server_url}/chat/chatrooms/{chatroom_id}/messages",
            params={"user_id": user_id, "limit": limit, "skip": skip},
        )

        if response.status_code == 200:
            return response.json().get("messages", [])
        else:
            log.error(f"Failed to get messages: {response.status_code}")
            return []
    except Exception as e:
        log.error(f"Failed to get messages: {e}")
        return []


def send_message(chatroom_id: str, user_id: str, content: str) -> bool:
    auth = get_auth()
    if not auth:
        return False

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.post(
            f"{config.settings.server_url}/chat/messages",
            json={
                "chatroom_id": chatroom_id,
                "sender_id": user_id,
                "content": content,
            },
            headers=headers,
        )

        if response.status_code == 200:
            return True
        else:
            log.error(
                f"Failed to send message: {response.status_code}\n{response.text}"
            )
            return False
    except Exception as e:
        log.error(f"Failed to send message: {e}")
        return False
