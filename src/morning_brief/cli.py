"""Command-line interface for Morning Brief."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, cast

import cyclopts

app = cyclopts.App(help="Generate and deliver a modular morning briefing.")


@app.command
def preview() -> None:
    """Print today's morning brief without posting it to Discord."""

    print(_build_brief())


@app.command
def run() -> None:
    """Generate today's morning brief and post it to Discord."""

    config = _load_config()
    if config.discord_bot_token is None:
        raise cyclopts.ValidationError(
            "DISCORD_BOT_TOKEN is required to post to Discord"
        )

    discord = import_module("morning_brief.delivery.discord")
    discord.send_discord_message(
        bot_token=config.discord_bot_token,
        channel_id=config.discord_channel_id,
        content=_build_brief(),
    )
    print(f"Posted Morning Brief to Discord channel {config.discord_channel_id}.")


@app.command(name="install-schedule")
def install_schedule(
    time: str = "06:00",
    timezone: str = "America/New_York",
    project_dir: Path | None = None,
) -> None:
    """Install and enable a systemd user timer for daily Morning Brief delivery."""

    config = _load_config()
    if project_dir is None:
        project_dir = Path.cwd()

    scheduler = import_module("morning_brief.scheduler")
    result = scheduler.install_schedule(
        project_dir=project_dir,
        time_of_day=time or config.schedule_time,
        timezone=timezone or config.timezone,
    )
    print(f"Installed {result.service_path}")
    print(f"Installed and enabled {result.timer_path}")


@app.command(name="uninstall-schedule")
def uninstall_schedule() -> None:
    """Disable and remove the systemd user timer for Morning Brief."""

    scheduler = import_module("morning_brief.scheduler")
    result = scheduler.uninstall_schedule()
    print(f"Removed {result.timer_path}")
    print(f"Removed {result.service_path}")


def main() -> None:
    """Run the Morning Brief CLI."""

    app()


def _build_brief() -> str:
    briefing = import_module("morning_brief.briefing")
    return cast(str, briefing.build_brief())


def _load_config() -> Any:
    config_module = import_module("morning_brief.config")
    return config_module.load_config()
