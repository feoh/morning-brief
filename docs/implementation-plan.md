## Context

The user wants a new personal project called **Morning Brief** under `/home/feoh/src/personal`. Its purpose is to send a daily morning report containing information of interest, designed to grow modularly over time. The initial delivery target is Discord, reusing the OpenClaw-style Discord bot setup (`DISCORD_BOT_TOKEN` in `.env`) but posting to `#morning-brief` with channel ID `1510832637407662142`. The first briefing module should report current prices for AMZN, GOOG, AAPL, MSFT, Bitcoin, and Ethereum. The user also wants scheduling built into the program and wants a copy of this plan written into the GitHub repository once the project repo is created.

## Goals / Non-goals

- Goals:
  - Create a new uv-managed Python project named `morning-brief`.
  - Provide a modular architecture so future briefing modules and delivery channels can be added cleanly.
  - Implement an initial markets module for stocks `AMZN`, `GOOG`, `AAPL`, `MSFT` and crypto `BTC`/`ETH`.
  - Deliver the morning briefing to Discord using the bot token from environment configuration.
  - Default Discord channel ID to `1510832637407662142`, while allowing environment override.
  - Provide CLI commands to run, preview, install a user-level schedule, and uninstall that schedule.
  - Use a systemd user timer for scheduling, defaulting to 6:00 AM Eastern unless overridden.
  - Once the GitHub/project repository exists, include a copy of this implementation plan in it.

- Non-goals:
  - Do not migrate or revive OpenClaw itself.
  - Do not commit secrets or hardcode the Discord bot token.
  - Do not implement additional briefing categories beyond market prices in the initial version.
  - Do not require Discord channel-name discovery at runtime.

## Files to change

- `morning-brief/pyproject.toml` — define the uv Python project, dependencies, package settings, and CLI entrypoint.
- `morning-brief/README.md` — document setup, environment variables, preview/run usage, Discord channel configuration, and scheduling commands.
- `morning-brief/.env.example` — show required `DISCORD_BOT_TOKEN` and optional `DISCORD_CHANNEL_ID`/schedule-related configuration without real secrets.
- `morning-brief/docs/implementation-plan.md` — copy this agreed implementation plan into the project repository once it exists.
- `morning-brief/src/morning_brief/__init__.py` — package marker/version location if needed.
- `morning-brief/src/morning_brief/config.py` — load environment configuration, including Discord token and default channel ID.
- `morning-brief/src/morning_brief/briefing.py` — orchestrate enabled briefing modules into one formatted report.
- `morning-brief/src/morning_brief/modules/base.py` — define the interface/protocol for briefing modules.
- `morning-brief/src/morning_brief/modules/markets.py` — fetch and format stock/crypto price data.
- `morning-brief/src/morning_brief/delivery/discord.py` — send formatted briefings to Discord.
- `morning-brief/src/morning_brief/scheduler.py` — create/remove systemd user service and timer files for scheduled runs.
- `morning-brief/src/morning_brief/cli.py` — implement Cyclopts CLI commands: run, preview, install-schedule, uninstall-schedule.
- `morning-brief/tests/` — add focused tests for formatting/config behavior and scheduler file generation where practical.

## Ordered steps

1. Create the `morning-brief` project directory and initialize it as a uv Python project.
2. Add dependencies appropriate for the agreed design: Cyclopts for the CLI, environment loading, HTTP/Discord integration, and market price retrieval.
3. Create the package skeleton under `src/morning_brief/` with separate modules for config, briefing orchestration, briefing modules, Discord delivery, scheduling, and CLI commands.
4. Copy this implementation plan into the project repository, e.g. `docs/implementation-plan.md`, after the repository/project structure has been created.
5. Implement configuration loading:
   - Read `DISCORD_BOT_TOKEN` from environment or `.env`.
   - Use `1510832637407662142` as the default Discord channel ID.
   - Allow `DISCORD_CHANNEL_ID` to override the default.
6. Implement the modular briefing interface and the initial markets module.
7. Implement market price retrieval for `AMZN`, `GOOG`, `AAPL`, `MSFT`, `BTC-USD`, and `ETH-USD`, with output labels Bitcoin and Ethereum for the crypto entries.
8. Implement report composition into a concise Discord-friendly Markdown message.
9. Implement Discord delivery using the configured bot token and channel ID.
10. Implement the Cyclopts CLI:
   - `preview` prints the generated brief to stdout without posting.
   - `run` generates and posts the brief to Discord.
   - `install-schedule --time 06:00` installs/enables a systemd user timer.
   - `uninstall-schedule` disables/removes the installed user timer/service.
11. Implement systemd user timer generation in the scheduler, using a default daily 6:00 AM Eastern schedule unless the user provides another time.
12. Add `.env.example` and README setup instructions, including how to set the bot token, how the default channel ID works, how to preview, how to run, and how to inspect timer logs with `journalctl --user -u morning-brief.service`.
13. Add focused tests for code that can be tested without contacting external services, especially config defaults, report formatting, and scheduler unit contents.
14. Run validation commands and fix issues before considering the implementation complete.

## Validation

- `uv sync`
- Confirm `morning-brief/docs/implementation-plan.md` exists once the project repository is created.
- `uv run morning-brief preview` to confirm a briefing renders without posting to Discord.
- `uv run morning-brief run` only after `DISCORD_BOT_TOKEN` is configured, to confirm posting to channel ID `1510832637407662142`.
- `uv run morning-brief install-schedule --time 06:00` followed by systemd user checks such as `systemctl --user status morning-brief.timer`.
- `journalctl --user -u morning-brief.service` to inspect scheduled-run logs after a manual or timer-triggered run.
- `uv run pytest` if tests are added.
- `uv run pre-commit run --all-files` and `uv run mypy morning_brief` if those tools are configured for the project.

## Risks & unknowns

- The Discord bot token is not present in committed files and must be supplied locally via `.env` or environment variables.
- Market data provider choice is not fully locked; implementation should use a practical Yahoo Finance-compatible source such as `yfinance` or a direct Yahoo chart API.
- Network/API failures from market data or Discord need graceful handling so one failed lookup does not make the whole briefing unusable.
- systemd user timers assume the target machine supports user-level systemd services and has the needed environment available to the service.
- Exact formatting of the market report was not specified beyond including current prices for the requested assets.
