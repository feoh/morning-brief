"""Discord delivery backend."""

from __future__ import annotations

import requests

DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_MESSAGE_LIMIT = 2000


class DiscordDeliveryError(RuntimeError):
    """Raised when Discord message delivery fails."""


def send_discord_message(bot_token: str, channel_id: str, content: str) -> None:
    """Send content to a Discord channel using a bot token."""

    if not bot_token:
        raise DiscordDeliveryError("DISCORD_BOT_TOKEN is required to post to Discord")

    for chunk in _chunk_message(content):
        response = requests.post(
            f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
            headers={
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json",
            },
            json={"content": chunk},
            timeout=15,
        )
        if response.status_code >= 400:
            raise DiscordDeliveryError(
                f"Discord API returned {response.status_code}: {response.text}"
            )


def _chunk_message(content: str) -> list[str]:
    """Split long messages to stay below Discord's message-size limit."""

    chunks: list[str] = []
    current = ""
    for block in _message_blocks(content):
        candidate = f"{current}\n{block}" if current else block
        if len(candidate) > DISCORD_MESSAGE_LIMIT:
            if current:
                chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _message_blocks(content: str) -> list[str]:
    """Return chunks no larger than the Discord message limit, preferring line breaks."""

    blocks: list[str] = []
    for line in content.splitlines():
        if len(line) <= DISCORD_MESSAGE_LIMIT:
            blocks.append(line)
            continue
        blocks.extend(
            line[start : start + DISCORD_MESSAGE_LIMIT]
            for start in range(0, len(line), DISCORD_MESSAGE_LIMIT)
        )
    return blocks
