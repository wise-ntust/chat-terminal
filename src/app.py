import os
import threading
import time

from textual import events, log
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ListItem, ListView, RichLog

from .auth import get_auth, login_flow
from .chat import fetch_chatrooms, fetch_messages, format_message, send_message
from .config import config
from .friends import (
    accept_friend_request,
    delete_friend,
    fetch_friend_requests,
    fetch_friends,
    reject_friend_request,
    send_friend_request,
)


class FriendModal(ModalScreen):
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = None
        self.friends = []

    def compose(self) -> ComposeResult:
        yield Container(
            ListView(id="listview-friend-modal"),
            Input(id="input-add-friend", placeholder="Enter friend's email"),
            Button("Close", id="button-close-modal"),
            id="container-friend-modal",
        )

    def on_mount(self) -> None:
        self._update_listview()

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            if not self.query_one(Input).value:
                return
            self._add_friend(self.query_one(Input).value)
            self.query_one(Input).value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "button-close-modal":
            self.app.pop_screen()
        elif event.button.id == "button-del-friend":
            list_item_id = event.button.parent.parent.id
            friend_id = self.friends[int(list_item_id.split("-")[-1])]["id"]
            self._del_friend(friend_id)
        elif event.button.id == "button-accept-friend-request":
            list_item_id = event.button.parent.parent.id
            friend_id = self.friend_requests[int(list_item_id.split("-")[-1])]["id"]
            self._accept_friend_request(friend_id)
        elif event.button.id == "button-reject-friend-request":
            list_item_id = event.button.parent.parent.id
            friend_id = self.friend_requests[int(list_item_id.split("-")[-1])]["id"]
            self._reject_friend_request(friend_id)

    def _update_listview(self) -> None:
        self.query_one("#listview-friend-modal").clear()
        timestamp = int(time.time())

        self.friend_requests = fetch_friend_requests(self.user_id)
        for i, friend_request in enumerate(self.friend_requests):
            self.query_one("#listview-friend-modal").append(
                ListItem(
                    Grid(
                        Label(friend_request["name"], id="label-friend-name"),
                        Button("Accept", id=f"button-accept-friend-request"),
                        Button("Reject", id=f"button-reject-friend-request"),
                        id="grid-friend-request-item",
                    ),
                    id=f"modal-friend-request-{timestamp}-{i}",
                )
            )

        self.friends = fetch_friends(self.user_id)
        for i, friend in enumerate(self.friends):
            self.query_one("#listview-friend-modal").append(
                ListItem(
                    Grid(
                        Label(friend["name"], id="label-friend-name"),
                        Button("Delete", id=f"button-del-friend"),
                        id="grid-friend-item",
                    ),
                    id=f"modal-friend-{timestamp}-{i}",
                )
            )

    def _add_friend(self, email: str) -> None:
        response = send_friend_request(email)
        if not response:
            self.notify("Error sending friend request")
            return

        if response.status_code == 200:
            self.notify("Successfully sent friend request")
        else:
            self.notify(response.json().get("detail"))

    def _del_friend(self, friend_id: str) -> None:
        response = delete_friend(friend_id)
        if not response:
            self.notify("Failed to delete friend")
            return

        if response.status_code == 200:
            self.notify("Successfully deleted friend")
        else:
            self.notify(response.json().get("detail"))

        self._update_listview()

    def _accept_friend_request(self, friend_id: str) -> None:
        response = accept_friend_request(friend_id)
        if not response:
            self.notify("Failed to accept friend request")
            return

        if response.status_code == 200:
            self.notify("Successfully accepted friend request")
        else:
            self.notify(response.json().get("detail"))

        self._update_listview()

    def _reject_friend_request(self, friend_id: str) -> None:
        response = reject_friend_request(friend_id)
        if not response:
            self.notify("Failed to reject friend request")
            return

        if response.status_code == 200:
            self.notify("Successfully rejected friend request")
        else:
            self.notify(response.json().get("detail"))

        self._update_listview()


class ChatApp(App):
    CSS_PATH = "app.css"

    def __init__(self):
        super().__init__()
        self.chatroom_id = None
        self.user_id = None
        self.chatrooms = []
        self.friends = []
        self.should_update = False
        self.update_thread = None

    def compose(self) -> ComposeResult:
        yield Horizontal(
            Vertical(
                ListView(id="listview-friend"),
                Button(label="Friends", id="button-friends"),
                Button(label="Login", id="button-login"),
                id="sidebar",
            ),
            Vertical(
                RichLog(wrap=True, markup=True, id="richlog-message"),
                Input(
                    type="text",
                    placeholder="Aa",
                    id="input-message",
                ).focus(),
                id="main",
            ),
        )

    def on_mount(self) -> None:
        self._update_app()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item.id.startswith("friend-"):
            selected_id = int(event.item.id.split("-")[-1])
            self.chatroom_id = self.friends[selected_id]["chatroom_id"]
            self._update_messages()

            # Stop existing update thread if any
            if self.update_thread and self.should_update:
                self.should_update = False
                self.update_thread.join()

            # Start new update thread
            self.should_update = True
            self.update_thread = threading.Thread(target=self._background_update)
            self.update_thread.daemon = True  # 讓線程隨主程式結束而結束
            self.update_thread.start()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "button-friends":
            # Stop message updates before opening modal
            if self.update_thread and self.should_update:
                self.should_update = False
                self.update_thread.join()
            self.push_screen(FriendModal(self.user_id))
        elif event.button.id == "button-login":
            result = login_flow()
            if result["status"] == "failed":
                self.notify(result["message"])
            else:
                self.notify("Login successful")
            self._update_app()

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._send_message(self.query_one(Input).value)
            self.query_one(Input).value = ""

    def on_screen_resume(self) -> None:
        # Resume message updates when returning from modal
        if self.chatroom_id:
            self.should_update = True
            self.update_thread = threading.Thread(target=self._background_update)
            self.update_thread.daemon = True
            self.update_thread.start()

    def on_unmount(self) -> None:
        """Called when the app is about to be unmounted."""
        try:
            # Stop update thread if running
            if self.update_thread and self.should_update:
                self.should_update = False
                if self.update_thread.is_alive():
                    self.update_thread.join(timeout=1.0)  # 設定超時時間避免卡住
        except Exception:
            pass  # 忽略清理過程中的錯誤

    def _background_update(self):
        while self.should_update:
            self._update_messages()
            time.sleep(config.settings.refresh_interval)

    def _update_messages(self):
        try:
            richlog = self.query_one("#richlog-message")
            messages_list = fetch_messages(self.chatroom_id, self.user_id)
            messages_list.reverse()
            messages = "\n".join(
                [format_message(msg, self.user_id) for msg in messages_list]
            )
            richlog.clear()
            richlog.write(messages)
        except Exception as e:
            self.notify(f"Error updating messages: {str(e)}")

    def _update_friends(self):
        self.query_one("#listview-friend").clear()
        self.friends = fetch_friends(self.user_id)

        timestamp = int(time.time())
        for i, friend in enumerate(self.friends):
            self.query_one("#listview-friend").append(
                ListItem(Label(friend["name"]), id=f"friend-{timestamp}-{i}")
            )

    def _send_message(self, content: str):
        if not content.strip():
            return

        if not send_message(self.chatroom_id, self.user_id, content):
            self.query_one("#richlog-message").write("send message failed")
            return

        self._update_messages()

    def _update_app(self):
        auth = get_auth()
        if not auth:
            return

        try:
            if self.update_thread and self.should_update:
                self.should_update = False
                if self.update_thread.is_alive():
                    self.update_thread.join(timeout=1.0)
        except Exception:
            pass

        self.user_id = auth.get("user_id")
        self.chatroom_id = None
        self.chatrooms = []
        self.friends = []
        self.query_one("#listview-friend").clear()
        self.query_one("#richlog-message").clear()
        self._update_friends()


def start():
    app = ChatApp()
    app.run()


if __name__ == "__main__":
    start()
