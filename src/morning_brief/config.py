"""Configuration loading for Morning Brief."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

DEFAULT_DAILY_FIREHOSE_API_URL = "http://127.0.0.1:8000"
DEFAULT_DAILY_FIREHOSE_PUBLIC_URL = "https://daily-firehose.reedfish-regulus.ts.net"
DEFAULT_DISCORD_CHANNEL_ID = "1510832637407662142"
DEFAULT_NEWS_HEADLINE_LIMIT = 5
DEFAULT_RSS_ARTICLE_LIMIT = 20
DEFAULT_TODOIST_TASK_LIMIT = 20
DEFAULT_SCHEDULE_TIME = "06:00"
DEFAULT_TIMEZONE = "America/New_York"


@dataclass(frozen=True)
class Config:
    """Runtime configuration for Morning Brief."""

    discord_bot_token: str | None
    discord_channel_id: str = DEFAULT_DISCORD_CHANNEL_ID
    daily_firehose_api_url: str = DEFAULT_DAILY_FIREHOSE_API_URL
    daily_firehose_public_url: str = DEFAULT_DAILY_FIREHOSE_PUBLIC_URL
    daily_firehose_api_token: str | None = None
    agent_link_secret: str | None = None
    rss_article_limit: int = DEFAULT_RSS_ARTICLE_LIMIT
    news_headline_limit: int = DEFAULT_NEWS_HEADLINE_LIMIT
    todoist_api_token: str | None = None
    todoist_task_limit: int = DEFAULT_TODOIST_TASK_LIMIT
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
        daily_firehose_api_url=os.getenv(
            "DAILY_FIREHOSE_API_URL", DEFAULT_DAILY_FIREHOSE_API_URL
        ).rstrip("/"),
        daily_firehose_public_url=os.getenv(
            "DAILY_FIREHOSE_PUBLIC_URL", DEFAULT_DAILY_FIREHOSE_PUBLIC_URL
        ).rstrip("/"),
        daily_firehose_api_token=os.getenv("DAILY_FIREHOSE_API_TOKEN"),
        agent_link_secret=os.getenv("AGENT_LINK_SECRET"),
        rss_article_limit=int(
            os.getenv("MORNING_BRIEF_RSS_ARTICLE_LIMIT", str(DEFAULT_RSS_ARTICLE_LIMIT))
        ),
        news_headline_limit=int(
            os.getenv(
                "MORNING_BRIEF_NEWS_HEADLINE_LIMIT",
                str(DEFAULT_NEWS_HEADLINE_LIMIT),
            )
        ),
        todoist_api_token=os.getenv("TODOIST_API_TOKEN") or os.getenv("TODOIST_API_KEY"),
        todoist_task_limit=int(
            os.getenv(
                "MORNING_BRIEF_TODOIST_TASK_LIMIT",
                str(DEFAULT_TODOIST_TASK_LIMIT),
            )
        ),
        schedule_time=os.getenv("MORNING_BRIEF_TIME", DEFAULT_SCHEDULE_TIME),
        timezone=os.getenv("MORNING_BRIEF_TIMEZONE", DEFAULT_TIMEZONE),
    )
