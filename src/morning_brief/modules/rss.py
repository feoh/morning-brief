"""Daily Firehose RSS briefing module."""

from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import dataclass
import hmac
from typing import Any
from urllib.parse import urlencode

import requests

from .base import BriefSection


@dataclass(frozen=True)
class RssArticle:
    """One Daily Firehose article for the morning brief."""

    article_id: int
    title: str
    url: str
    feed_title: str
    published_at: str | None = None
    save_url: str | None = None


class DailyFirehoseModule:
    """Build a briefing section from today's Daily Firehose RSS articles."""

    name = "daily-firehose-rss"

    def __init__(
        self,
        api_url: str,
        public_url: str,
        api_token: str | None,
        agent_link_secret: str | None,
        article_limit: int = 20,
    ) -> None:
        self.api_url = api_url.rstrip("/")
        self.public_url = public_url.rstrip("/")
        self.api_token = api_token
        self.agent_link_secret = agent_link_secret
        self.article_limit = article_limit

    def build_section(self) -> BriefSection:
        """Build the RSS article section."""

        if not self.api_token:
            return BriefSection(
                title="RSS Feed Updates",
                body="Daily Firehose API token is not configured.",
            )

        try:
            articles = fetch_daily_firehose_articles(
                api_url=self.api_url,
                public_url=self.public_url,
                api_token=self.api_token,
                agent_link_secret=self.agent_link_secret,
                article_limit=self.article_limit,
            )
        except requests.RequestException as exc:
            return BriefSection(
                title="RSS Feed Updates",
                body=f"Daily Firehose API request failed: {exc}",
            )
        except (KeyError, TypeError, ValueError) as exc:
            return BriefSection(
                title="RSS Feed Updates",
                body=f"Daily Firehose API response could not be parsed: {exc}",
            )

        mark_read_url = None
        if self.agent_link_secret:
            mark_read_url = signed_mark_period_read_url(
                public_url=self.public_url,
                scope="day",
                agent_link_secret=self.agent_link_secret,
            )

        return BriefSection(
            title="RSS Feed Updates",
            body=format_rss_articles(articles, mark_read_url=mark_read_url),
        )


def fetch_daily_firehose_articles(
    *,
    api_url: str,
    public_url: str,
    api_token: str,
    agent_link_secret: str | None,
    article_limit: int,
) -> list[RssArticle]:
    """Fetch today's unread/unsaved Daily Firehose articles."""

    response = requests.get(
        f"{api_url.rstrip('/')}/api/v1/briefing/morning/",
        headers={"Authorization": f"Bearer {api_token}"},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    raw_articles = payload["articles"][:article_limit]
    return [
        _article_from_payload(
            raw_article,
            public_url=public_url,
            agent_link_secret=agent_link_secret,
        )
        for raw_article in raw_articles
    ]


def _article_from_payload(
    payload: dict[str, Any],
    *,
    public_url: str,
    agent_link_secret: str | None,
) -> RssArticle:
    article_id = int(payload["id"])
    feed = payload.get("feed") or {}
    save_url = None
    if agent_link_secret:
        save_url = signed_save_and_go_url(
            public_url=public_url,
            article_id=article_id,
            agent_link_secret=agent_link_secret,
        )
    return RssArticle(
        article_id=article_id,
        title=str(payload["title"]),
        url=str(payload["url"]),
        feed_title=str(feed.get("title") or "Unknown feed"),
        published_at=payload.get("published_at"),
        save_url=save_url,
    )


def signed_save_and_go_url(
    *, public_url: str, article_id: int, agent_link_secret: str
) -> str:
    """Build a Daily Firehose link that saves an article, then redirects to it."""

    signature = hmac.new(
        agent_link_secret.encode(),
        f"save-and-go:{article_id}".encode(),
        "sha256",
    ).hexdigest()
    query = urlencode({"sig": signature})
    return f"{public_url.rstrip('/')}/api/v1/articles/{article_id}/save-and-go/?{query}"


def signed_mark_period_read_url(
    *, public_url: str, scope: str, agent_link_secret: str
) -> str:
    """Build a Daily Firehose link that marks a period read."""

    signature = hmac.new(
        agent_link_secret.encode(),
        f"mark-period-read:{scope}".encode(),
        "sha256",
    ).hexdigest()
    query = urlencode({"scope": scope, "sig": signature})
    return f"{public_url.rstrip('/')}/api/v1/mark-period-read-and-go/?{query}"


def format_rss_articles(
    articles: list[RssArticle], *, mark_read_url: str | None = None
) -> str:
    """Format RSS articles as Discord-friendly Markdown."""

    if not articles:
        return "No new unread articles in Daily Firehose today."

    lines = [f"_As of {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_", ""]
    for article in articles:
        target = article.save_url or article.url
        lines.append(f"- [{article.title}]({target}) — {article.feed_title}")
    if mark_read_url:
        lines.extend(["", f"[Mark all of today's articles as read]({mark_read_url})"])
    return "\n".join(lines)
