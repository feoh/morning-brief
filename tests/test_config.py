from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, cast


def _config_module() -> Any:
    return import_module("morning_brief.config")


def test_load_config_defaults(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)
    monkeypatch.delenv("DAILY_FIREHOSE_API_TOKEN", raising=False)
    config_module = _config_module()

    config = config_module.load_config(tmp_path / ".env")

    assert config.discord_bot_token is None
    assert config.discord_channel_id == config_module.DEFAULT_DISCORD_CHANNEL_ID
    assert config.daily_firehose_api_url == config_module.DEFAULT_DAILY_FIREHOSE_API_URL
    assert config.daily_firehose_api_token is None


def test_load_config_from_env_file(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)
    monkeypatch.delenv("DAILY_FIREHOSE_API_TOKEN", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=test-token\n"
        "DISCORD_CHANNEL_ID=123\n"
        "DAILY_FIREHOSE_API_TOKEN=api-token\n"
        "AGENT_LINK_SECRET=link-secret\n"
        "MORNING_BRIEF_RSS_ARTICLE_LIMIT=5\n"
        "MORNING_BRIEF_TIME=07:15\n"
    )
    config_module = _config_module()

    config = cast(Any, config_module.load_config(env_file))

    assert config.discord_bot_token == "test-token"
    assert config.discord_channel_id == "123"
    assert config.daily_firehose_api_token == "api-token"
    assert config.agent_link_secret == "link-secret"
    assert config.rss_article_limit == 5
    assert config.schedule_time == "07:15"
