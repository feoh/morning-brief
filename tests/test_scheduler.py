from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any


def _scheduler_module() -> Any:
    return import_module("morning_brief.scheduler")


def test_service_unit_uses_project_dir() -> None:
    scheduler = _scheduler_module()
    unit = scheduler.service_unit(Path("/tmp/morning-brief"))

    assert "WorkingDirectory=/tmp/morning-brief" in unit
    assert "EnvironmentFile=-/tmp/morning-brief/.env" in unit
    assert "morning-brief run" in unit


def test_timer_unit_defaults_to_morning_eastern() -> None:
    scheduler = _scheduler_module()
    unit = scheduler.timer_unit()

    assert "OnCalendar=*-*-* 06:00:00 America/New_York" in unit
    assert "Persistent=true" in unit


def test_install_and_uninstall_schedule_without_systemctl(tmp_path: Path) -> None:
    scheduler = _scheduler_module()
    result = scheduler.install_schedule(
        project_dir=Path("/tmp/morning-brief"),
        systemd_user_dir=tmp_path,
        enable=False,
    )

    assert result.service_path.exists()
    assert result.timer_path.exists()

    scheduler.uninstall_schedule(systemd_user_dir=tmp_path, disable=False)

    assert not result.service_path.exists()
    assert not result.timer_path.exists()
