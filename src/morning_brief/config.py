"""Configuration loading for Morning Brief."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

DEFAULT_DISCORD_CHANNEL_ID = "1510832637407662142"
DEFAULT_SCHEDULE_TIME = "06:00"
DEFAULT_TIMEZONE = "America/New_York"


@dataclass(frozen=True)
class Config:
    """Runtime configuration for Morning Brief."""

    discord_bot_token: str | None
    discord_channel_id: str = DEFAULT_DISCORD_CHANNEL_ID
    schedule_time: str = DEFAULT_SCHEDULE_TIME
    timezone: str = DEFAULT_TIMEZONE


def _load_env_file(env_file: Path) -> None:
    """Load simple KEY=VALUE entries from env_file without overwriting the environment."""

    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_config(env_file: Path | None = None) -> Config:
    """Load configuration from environment variables and an optional .env file."""

    if env_file is None:
        env_file = Path.cwd() / ".env"

    _load_env_file(env_file)

    return Config(
        discord_bot_token=os.getenv("DISCORD_BOT_TOKEN"),
        discord_channel_id=os.getenv("DISCORD_CHANNEL_ID", DEFAULT_DISCORD_CHANNEL_ID),
        schedule_time=os.getenv("MORNING_BRIEF_TIME", DEFAULT_SCHEDULE_TIME),
        timezone=os.getenv("MORNING_BRIEF_TIMEZONE", DEFAULT_TIMEZONE),
    )
