from __future__ import annotations

from importlib import import_module
from urllib.parse import parse_qs, urlparse


def test_signed_save_and_go_url() -> None:
    rss = import_module("morning_brief.modules.rss")

    url = rss.signed_save_and_go_url(
        public_url="https://daily-firehose.example.com",
        article_id=42,
        agent_link_secret="test-secret",
    )

    parsed = urlparse(url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "daily-firehose.example.com"
    assert parsed.path == "/api/v1/articles/42/save-and-go/"
    assert parse_qs(parsed.query)["sig"] == [
        "7c958f7170da8fb8a3f4f884357887e87c869fec3c0aeb9a7596f3ac484629f1"
    ]


def test_format_rss_articles_uses_save_links() -> None:
    rss = import_module("morning_brief.modules.rss")
    articles = [
        rss.RssArticle(
            article_id=1,
            title="An article",
            url="https://example.com/article",
            feed_title="Example Feed",
            save_url="https://daily-firehose.example.com/save",
        )
    ]

    output = rss.format_rss_articles(articles)

    assert (
        "[An article](https://daily-firehose.example.com/save) — Example Feed" in output
    )


def test_format_rss_articles_handles_empty_list() -> None:
    rss = import_module("morning_brief.modules.rss")

    assert (
        rss.format_rss_articles([]) == "No new unread articles in Daily Firehose today."
    )
