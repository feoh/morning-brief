"""Top news headlines briefing module."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
import html
import re
import xml.etree.ElementTree as ET
from typing import Literal

import requests

from .base import BriefSection

Bias = Literal["liberal", "conservative", "neutral"]

BIAS_ICONS: dict[Bias, str] = {
    "liberal": "🔵",
    "conservative": "🔴",
    "neutral": "⚪",
}

BIAS_LABELS: dict[Bias, str] = {
    "liberal": "left-leaning source",
    "conservative": "right-leaning source",
    "neutral": "neutral / wire / international source",
}


@dataclass(frozen=True)
class NewsSource:
    """A curated RSS source with source-level bias metadata."""

    name: str
    url: str
    bias: Bias


@dataclass(frozen=True)
class NewsHeadline:
    """A single news headline from a curated source."""

    title: str
    url: str
    source: NewsSource
    published_at: datetime | None = None


DEFAULT_NEWS_SOURCES = (
    NewsSource("AP Top News", "https://apnews.com/hub/ap-top-news?output=rss", "neutral"),
    NewsSource("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml", "neutral"),
    NewsSource(
        "Reuters World",
        "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
        "neutral",
    ),
    NewsSource("The Guardian US", "https://www.theguardian.com/us-news/rss", "liberal"),
    NewsSource("NPR News", "https://feeds.npr.org/1001/rss.xml", "liberal"),
    NewsSource(
        "Fox News Politics",
        "https://moxie.foxnews.com/google-publisher/politics.xml",
        "conservative",
    ),
    NewsSource("National Review", "https://www.nationalreview.com/feed/", "conservative"),
)


class TopNewsModule:
    """Build a top-headlines section across a curated political spectrum."""

    name = "top-news"

    def __init__(
        self,
        sources: tuple[NewsSource, ...] = DEFAULT_NEWS_SOURCES,
        headline_limit: int = 5,
    ) -> None:
        self.sources = sources
        self.headline_limit = headline_limit

    def build_section(self) -> BriefSection:
        """Build the top news section."""

        headlines = fetch_all_headlines(self.sources)
        selected = select_top_headlines(headlines, limit=self.headline_limit)
        return BriefSection(title="Top News Headlines", body=format_headlines(selected))


def fetch_all_headlines(sources: tuple[NewsSource, ...]) -> list[NewsHeadline]:
    """Fetch recent headlines from every configured news source.

    One unavailable feed should not prevent the whole section from rendering.
    """

    headlines: list[NewsHeadline] = []
    cutoff = datetime.now(UTC) - timedelta(hours=30)
    for source in sources:
        try:
            source_headlines = fetch_source_headlines(source)
        except (requests.RequestException, ET.ParseError):
            continue
        for headline in source_headlines:
            if headline.published_at is None or headline.published_at >= cutoff:
                headlines.append(headline)
    return headlines


def fetch_source_headlines(source: NewsSource, per_source_limit: int = 5) -> list[NewsHeadline]:
    """Fetch and parse headlines from one RSS/Atom source."""

    response = requests.get(
        source.url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; morning-brief/0.1)"},
        timeout=20,
    )
    response.raise_for_status()
    return parse_feed(response.text, source)[:per_source_limit]


def parse_feed(content: str, source: NewsSource) -> list[NewsHeadline]:
    """Parse RSS or Atom feed content into headlines."""

    root = ET.fromstring(content)
    items = root.findall(".//item")
    if items:
        return [_headline_from_rss_item(item, source) for item in items]

    entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    return [_headline_from_atom_entry(entry, source) for entry in entries]


def select_top_headlines(headlines: list[NewsHeadline], limit: int = 5) -> list[NewsHeadline]:
    """Select a diverse set of recent headlines across source leanings."""

    remaining = sorted(headlines, key=_headline_sort_key, reverse=True)
    selected: list[NewsHeadline] = []
    seen_titles: set[str] = set()
    seen_sources: set[str] = set()

    for bias in ("neutral", "liberal", "conservative"):
        candidate = _pop_first_matching(
            remaining,
            _unseen_with_bias(bias, seen_titles),
        )
        if candidate is not None:
            _add_selected(candidate, selected, seen_titles, seen_sources)

    while len(selected) < limit and remaining:
        candidate = _pop_first_matching(
            remaining,
            lambda headline: _normalized_title(headline.title) not in seen_titles
            and headline.source.name not in seen_sources,
        ) or _pop_first_matching(
            remaining,
            lambda headline: _normalized_title(headline.title) not in seen_titles,
        )
        if candidate is None:
            break
        _add_selected(candidate, selected, seen_titles, seen_sources)

    return selected[:limit]


def format_headlines(headlines: list[NewsHeadline]) -> str:
    """Format selected headlines as Discord-friendly Markdown."""

    if not headlines:
        return "No recent headlines found across the curated news sources."

    lines = [
        "_Source-leaning icons: 🔵 left-leaning · 🔴 right-leaning · "
        "⚪ neutral/wire/international_",
        "",
    ]
    for headline in headlines:
        icon = BIAS_ICONS[headline.source.bias]
        label = BIAS_LABELS[headline.source.bias]
        lines.append(
            f"- {icon} [{headline.title}]({headline.url}) — "
            f"{headline.source.name} ({label})"
        )
    return "\n".join(lines)


def _unseen_with_bias(
    bias: Bias, seen_titles: set[str]
) -> Callable[[NewsHeadline], bool]:
    def predicate(headline: NewsHeadline) -> bool:
        return (
            headline.source.bias == bias
            and _normalized_title(headline.title) not in seen_titles
        )

    return predicate


def _add_selected(
    headline: NewsHeadline,
    selected: list[NewsHeadline],
    seen_titles: set[str],
    seen_sources: set[str],
) -> None:
    selected.append(headline)
    seen_titles.add(_normalized_title(headline.title))
    seen_sources.add(headline.source.name)


def _headline_from_rss_item(item: ET.Element, source: NewsSource) -> NewsHeadline:
    title = _element_text(item, "title") or "Untitled"
    url = _element_text(item, "link") or ""
    published = _element_text(item, "pubDate") or _element_text(item, "published")
    return NewsHeadline(
        title=html.unescape(title.strip()),
        url=url.strip(),
        source=source,
        published_at=_parse_datetime(published),
    )


def _headline_from_atom_entry(entry: ET.Element, source: NewsSource) -> NewsHeadline:
    title = _namespaced_text(entry, "title") or "Untitled"
    link = entry.find("{http://www.w3.org/2005/Atom}link")
    url = link.attrib.get("href", "") if link is not None else ""
    published = _namespaced_text(entry, "published") or _namespaced_text(entry, "updated")
    return NewsHeadline(
        title=html.unescape(title.strip()),
        url=url.strip(),
        source=source,
        published_at=_parse_datetime(published),
    )


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _element_text(parent: ET.Element, tag: str) -> str | None:
    child = parent.find(tag)
    return child.text if child is not None else None


def _namespaced_text(parent: ET.Element, tag: str) -> str | None:
    child = parent.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
    return child.text if child is not None else None


def _headline_sort_key(headline: NewsHeadline) -> datetime:
    return headline.published_at or datetime.min.replace(tzinfo=UTC)


def _normalized_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _pop_first_matching(
    headlines: list[NewsHeadline], predicate: Callable[[NewsHeadline], bool]
) -> NewsHeadline | None:
    for index, headline in enumerate(headlines):
        if predicate(headline):
            return headlines.pop(index)
    return None
