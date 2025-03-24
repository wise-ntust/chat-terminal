import textwrap
import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from textual import log


class AuthData(BaseModel):
    user_id: str
    session_token: str
    expires_at: Optional[int] = None


class Settings(BaseSettings):
    app_name: str = "chat-terminal"
    server_url: str = "https://chat-server-cfpa.onrender.com"
    refresh_interval: int = 1
    max_messages: int = 50
    time_format: str = "%H:%M:%S"


class AppConfig:
    def __init__(self):
        self.settings = Settings()
        self.config_dir = Path.home() / ".config" / self.settings.app_name
        self.auth_file = self.config_dir / "auth.json"
        self.settings_file = self.config_dir / "settings.toml"

        self.config_dir.mkdir(parents=True, exist_ok=True)

        self._load_settings()

    def _load_settings(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "rb") as f:
                    toml_settings = tomllib.load(f)

                for key, value in toml_settings.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)
            except Exception as e:
                log.error(f"Error loading settings: {e}")
        else:
            self._create_default_settings()

    def _create_default_settings(self):
        default_settings = textwrap.dedent(
            f"""
            server_url = "{self.settings.server_url}"
            refresh_interval = {self.settings.refresh_interval}
            max_messages = {self.settings.max_messages}
            time_format = "{self.settings.time_format}"
            """
        ).strip()
        try:
            self.settings_file.write_text(default_settings)
        except Exception as e:
            log.error(f"Error creating default settings: {e}")

    def get_auth(self) -> Optional[AuthData]:
        try:
            if not self.auth_file.exists():
                return None
            data = self.auth_file.read_text()
            return AuthData.parse_raw(data)
        except Exception:
            return None

    def save_auth(self, auth_data: dict) -> bool:
        try:
            auth = AuthData(**auth_data)
            self.auth_file.write_text(auth.json())
            return True
        except Exception:
            return False

    def clear_auth(self) -> bool:
        try:
            if self.auth_file.exists():
                self.auth_file.unlink()
            return True
        except Exception:
            return False


config = AppConfig()
