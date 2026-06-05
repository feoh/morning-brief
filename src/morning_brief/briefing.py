"""Briefing orchestration."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from zoneinfo import ZoneInfo

from .modules.base import BriefingModule


def default_modules() -> list[BriefingModule]:
    """Return the currently enabled briefing modules."""

    config_module = import_module("morning_brief.config")
    markets_module = import_module("morning_brief.modules.markets")
    news_module = import_module("morning_brief.modules.news")
    rss_module = import_module("morning_brief.modules.rss")
    todoist_module = import_module("morning_brief.modules.todoist")
    config = config_module.load_config()
    return [
        markets_module.MarketsModule(),
        news_module.TopNewsModule(headline_limit=config.news_headline_limit),
        rss_module.DailyFirehoseModule(
            api_url=config.daily_firehose_api_url,
            public_url=config.daily_firehose_public_url,
            api_token=config.daily_firehose_api_token,
            agent_link_secret=config.agent_link_secret,
            article_limit=config.rss_article_limit,
        ),
        todoist_module.TodoistModule(
            api_token=config.todoist_api_token,
            task_limit=config.todoist_task_limit,
            timezone=config.timezone,
        ),
    ]


def build_brief(modules: list[BriefingModule] | None = None) -> str:
    """Build a complete Discord-friendly morning brief."""

    if modules is None:
        modules = default_modules()

    today = datetime.now(ZoneInfo("America/New_York")).strftime("%A, %B %-d, %Y")
    sections = [module.build_section().render() for module in modules]
    return "\n\n".join([f"# Morning Brief — {today}", *sections])
