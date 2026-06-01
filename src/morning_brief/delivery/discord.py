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

    if len(content) <= DISCORD_MESSAGE_LIMIT:
        return [content]

    chunks: list[str] = []
    current = ""
    for paragraph in content.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) > DISCORD_MESSAGE_LIMIT:
            if current:
                chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
