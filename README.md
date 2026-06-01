# Morning Brief

Morning Brief is a modular daily briefing tool. It currently builds a market update for AMZN, GOOG, AAPL, MSFT, Bitcoin, and Ethereum, includes today's new Daily Firehose RSS articles, then can post it to Discord.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env` and set `DISCORD_BOT_TOKEN` to the bot token formerly used for the OpenClaw-style Discord bot setup.

The default Discord channel is `#morning-brief`:

```text
1510832637407662142
```

Override it with `DISCORD_CHANNEL_ID` only if the channel changes.

For RSS articles, set `DAILY_FIREHOSE_API_TOKEN` to a Daily Firehose bearer token and set the same `AGENT_LINK_SECRET` in both Morning Brief and Daily Firehose. Morning Brief fetches articles from `DAILY_FIREHOSE_API_URL` and creates signed public `save-and-go` links using `DAILY_FIREHOSE_PUBLIC_URL`. Clicking an RSS article link saves it through Daily Firehose, then redirects to the article.

## Usage

Preview without posting:

```bash
uv run morning-brief preview
```

Post to Discord:

```bash
uv run morning-brief run
```

## Scheduling

Install and enable a systemd user timer for 6:00 AM Eastern:

```bash
uv run morning-brief install-schedule --time 06:00
```

Use another local time or timezone if needed:

```bash
uv run morning-brief install-schedule --time 07:30 --timezone America/New_York
```

Check the timer:

```bash
systemctl --user status morning-brief.timer
```

Inspect run logs:

```bash
journalctl --user -u morning-brief.service
```

Remove the schedule:

```bash
uv run morning-brief uninstall-schedule
```

## Extending

Add new briefing sources by implementing `BriefingModule` from `morning_brief.modules.base` and returning a `BriefSection`. Enable modules in `morning_brief.briefing.default_modules()`.

Delivery backends live under `morning_brief.delivery`.

## Notes

- Secrets belong in `.env`; do not commit them.
- Market data comes from Yahoo Finance's chart API via `requests`.
- RSS article data comes from the local Daily Firehose API.
- `docs/implementation-plan.md` contains the agreed initial implementation plan.
