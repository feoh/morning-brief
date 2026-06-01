from __future__ import annotations

from datetime import UTC, datetime, timedelta
from importlib import import_module
from typing import Any


def _news() -> Any:
    return import_module("morning_brief.modules.news")


def test_parse_rss_feed() -> None:
    news = _news()
    source = news.NewsSource("Example News", "https://example.com/rss", "neutral")
    content = """
    <rss version="2.0">
      <channel>
        <item>
          <title>Example &amp;amp; headline</title>
          <link>https://example.com/story</link>
          <pubDate>Mon, 01 Jun 2026 10:00:00 GMT</pubDate>
        </item>
      </channel>
    </rss>
    """

    headlines = news.parse_feed(content, source)

    assert len(headlines) == 1
    assert headlines[0].title == "Example & headline"
    assert headlines[0].url == "https://example.com/story"
    assert headlines[0].source == source
    assert headlines[0].published_at == datetime(2026, 6, 1, 10, tzinfo=UTC)


def test_parse_atom_feed() -> None:
    news = _news()
    source = news.NewsSource("Atom News", "https://example.com/atom", "liberal")
    content = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Atom headline</title>
        <link href="https://example.com/atom-story" />
        <updated>2026-06-01T11:00:00Z</updated>
      </entry>
    </feed>
    """

    headlines = news.parse_feed(content, source)

    assert len(headlines) == 1
    assert headlines[0].title == "Atom headline"
    assert headlines[0].url == "https://example.com/atom-story"
    assert headlines[0].published_at == datetime(2026, 6, 1, 11, tzinfo=UTC)


def test_select_top_headlines_diversifies_bias_source_and_dedupes_titles() -> None:
    news = _news()
    now = datetime.now(UTC)
    neutral = news.NewsSource("AP", "https://example.com/ap", "neutral")
    liberal = news.NewsSource("NPR", "https://example.com/npr", "liberal")
    conservative = news.NewsSource("Fox", "https://example.com/fox", "conservative")
    other_neutral = news.NewsSource("BBC", "https://example.com/bbc", "neutral")
    headlines = [
        news.NewsHeadline("Shared Story!", "https://example.com/1", neutral, now),
        news.NewsHeadline(
            "Liberal Story",
            "https://example.com/2",
            liberal,
            now - timedelta(minutes=1),
        ),
        news.NewsHeadline(
            "Conservative Story",
            "https://example.com/3",
            conservative,
            now - timedelta(minutes=2),
        ),
        news.NewsHeadline(
            "Shared story",
            "https://example.com/4",
            other_neutral,
            now - timedelta(minutes=3),
        ),
        news.NewsHeadline(
            "World Story",
            "https://example.com/5",
            other_neutral,
            now - timedelta(minutes=4),
        ),
        news.NewsHeadline(
            "Another Story",
            "https://example.com/6",
            neutral,
            now - timedelta(minutes=5),
        ),
    ]

    selected = news.select_top_headlines(headlines, limit=5)

    assert [headline.title for headline in selected][:3] == [
        "Shared Story!",
        "Liberal Story",
        "Conservative Story",
    ]
    assert "Shared story" not in [headline.title for headline in selected]
    assert len(selected) == 5


def test_format_headlines_includes_bias_icons() -> None:
    news = _news()
    source = news.NewsSource("NPR", "https://example.com/npr", "liberal")
    headlines = [
        news.NewsHeadline(
            "A headline",
            "https://example.com/story",
            source,
            datetime(2026, 6, 1, tzinfo=UTC),
        )
    ]

    output = news.format_headlines(headlines)

    assert "🔵 [A headline](https://example.com/story) — NPR" in output
    assert "left-leaning source" in output
    assert "🔴 right-leaning" in output
    assert "⚪ neutral/wire/international" in output


def test_format_headlines_handles_empty_list() -> None:
    news = _news()

    assert (
        news.format_headlines([])
        == "No recent headlines found across the curated news sources."
    )
