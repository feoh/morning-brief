"""Briefing orchestration."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from zoneinfo import ZoneInfo

from .modules.base import BriefingModule


def default_modules() -> list[BriefingModule]:
    """Return the currently enabled briefing modules."""

    markets_module = import_module("morning_brief.modules.markets")
    return [markets_module.MarketsModule()]


def build_brief(modules: list[BriefingModule] | None = None) -> str:
    """Build a complete Discord-friendly morning brief."""

    if modules is None:
        modules = default_modules()

    today = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %-d, %Y")
    sections = [module.build_section().render() for module in modules]
    return "\n\n".join([f"# Morning Brief — {today}", *sections])
