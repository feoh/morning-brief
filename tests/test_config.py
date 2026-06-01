from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, cast


def _config_module() -> Any:
    return import_module("morning_brief.config")


def test_load_config_defaults(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)
    config_module = _config_module()

    config = config_module.load_config(tmp_path / ".env")

    assert config.discord_bot_token is None
    assert config.discord_channel_id == config_module.DEFAULT_DISCORD_CHANNEL_ID


def test_load_config_from_env_file(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    monkeypatch.delenv("DISCORD_CHANNEL_ID", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=test-token\nDISCORD_CHANNEL_ID=123\nMORNING_BRIEF_TIME=07:15\n"
    )
    config_module = _config_module()

    config = cast(Any, config_module.load_config(env_file))

    assert config.discord_bot_token == "test-token"
    assert config.discord_channel_id == "123"
    assert config.schedule_time == "07:15"
