from __future__ import annotations

from importlib import import_module


def test_chunk_message_splits_long_line_based_content() -> None:
    discord = import_module("morning_brief.delivery.discord")
    content = "# Heading\n" + "\n".join(f"- item {index} " + "x" * 100 for index in range(50))

    chunks = discord._chunk_message(content)

    assert len(chunks) > 1
    assert all(len(chunk) <= discord.DISCORD_MESSAGE_LIMIT for chunk in chunks)


def test_chunk_message_splits_single_oversized_line() -> None:
    discord = import_module("morning_brief.delivery.discord")
    content = "x" * (discord.DISCORD_MESSAGE_LIMIT + 1)

    chunks = discord._chunk_message(content)

    assert chunks == ["x" * discord.DISCORD_MESSAGE_LIMIT, "x"]
