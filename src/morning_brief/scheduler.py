"""systemd user timer management for Morning Brief."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

SERVICE_NAME = "morning-brief.service"
TIMER_NAME = "morning-brief.timer"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"


@dataclass(frozen=True)
class ScheduleInstallResult:
    """Information about installed schedule files."""

    service_path: Path
    timer_path: Path


def service_unit(project_dir: Path) -> str:
    """Return the systemd user service unit content."""

    uv_path = _command_path("uv")
    return f"""[Unit]
Description=Send the Morning Brief to Discord

[Service]
Type=oneshot
WorkingDirectory={project_dir}
ExecStart={uv_path} run morning-brief run
EnvironmentFile=-{project_dir}/.env
"""


def timer_unit(time_of_day: str = "06:00", timezone: str = "America/New_York") -> str:
    """Return the systemd user timer unit content."""

    return f"""[Unit]
Description=Run Morning Brief every morning

[Timer]
OnCalendar=*-*-* {time_of_day}:00 {timezone}
Persistent=true
Unit={SERVICE_NAME}

[Install]
WantedBy=timers.target
"""


def install_schedule(
    project_dir: Path,
    time_of_day: str = "06:00",
    timezone: str = "America/New_York",
    systemd_user_dir: Path = SYSTEMD_USER_DIR,
    enable: bool = True,
) -> ScheduleInstallResult:
    """Install and optionally enable the Morning Brief systemd user timer."""

    systemd_user_dir.mkdir(parents=True, exist_ok=True)
    service_path = systemd_user_dir / SERVICE_NAME
    timer_path = systemd_user_dir / TIMER_NAME

    service_path.write_text(service_unit(project_dir))
    timer_path.write_text(timer_unit(time_of_day, timezone))

    if enable:
        _run_systemctl("daemon-reload")
        _run_systemctl("enable", "--now", TIMER_NAME)

    return ScheduleInstallResult(service_path=service_path, timer_path=timer_path)


def uninstall_schedule(
    systemd_user_dir: Path = SYSTEMD_USER_DIR,
    disable: bool = True,
) -> ScheduleInstallResult:
    """Disable and remove the Morning Brief systemd user timer and service."""

    service_path = systemd_user_dir / SERVICE_NAME
    timer_path = systemd_user_dir / TIMER_NAME

    if disable:
        _run_systemctl("disable", "--now", TIMER_NAME, check=False)

    timer_path.unlink(missing_ok=True)
    service_path.unlink(missing_ok=True)

    if disable:
        _run_systemctl("daemon-reload", check=False)

    return ScheduleInstallResult(service_path=service_path, timer_path=timer_path)


def _run_systemctl(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a systemctl --user command."""

    return subprocess.run(
        ["systemctl", "--user", *args],
        check=check,
        text=True,
        capture_output=True,
    )


def _command_path(command: str) -> str:
    """Return a command path suitable for systemd ExecStart."""

    return shutil.which(command) or command
