from typing import Dict, List

import requests
from textual import log

from .auth import get_auth
from .config import config


def fetch_friends(user_id: str) -> List[Dict]:
    friends = list()

    auth = get_auth()
    if not auth:
        return friends

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.get(
            f"{config.settings.server_url}/friends/",
            params={"userId": user_id},
            headers=headers,
        )
        if response.status_code == 200:
            friends = response.json()
        else:
            log.error(f"Failed to get friends list: {response.status_code}")

    except Exception as e:
        log.error(f"Failed to get friends list: {e}")

    return friends


def fetch_friend_requests(user_id: str) -> List[Dict]:
    friend_requests = list()

    auth = get_auth()
    if not auth:
        return friend_requests

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.get(
            f"{config.settings.server_url}/friends/requests",
            params={"userId": user_id},
            headers=headers,
        )
        if response.status_code == 200:
            friend_requests = response.json()
        else:
            log.error(f"Failed to get friend requests: {response.status_code}")

    except Exception as e:
        log.error(f"Failed to get friend requests: {e}")

    return friend_requests


def send_friend_request(friend_email: str) -> requests.Response:
    auth = get_auth()
    if not auth:
        return None

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.post(
            f"{config.settings.server_url}/friends/?friend_email={friend_email}",
            headers=headers,
        )
        return response

    except Exception as e:
        return None


def accept_friend_request(friend_id: str) -> requests.Response:
    auth = get_auth()
    if not auth:
        return None

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.post(
            f"{config.settings.server_url}/friends/accept?friend_id={friend_id}",
            headers=headers,
        )
        return response

    except Exception as e:
        return None


def reject_friend_request(friend_id: str) -> requests.Response:
    auth = get_auth()
    if not auth:
        return None

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.post(
            f"{config.settings.server_url}/friends/reject?friend_id={friend_id}",
            headers=headers,
        )
        return response

    except Exception as e:
        return None


def delete_friend(friend_id: str) -> requests.Response:
    auth = get_auth()
    if not auth:
        return None

    session_token = auth.get("session_token")
    headers = {"Authorization": f"Bearer {session_token}"}

    try:
        response = requests.post(
            f"{config.settings.server_url}/friends/delete?friend_id={friend_id}",
            headers=headers,
        )
        return response

    except Exception as e:
        return None
