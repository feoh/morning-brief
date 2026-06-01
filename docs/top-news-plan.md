## Context

Morning Brief is an existing modular Python/uv project that posts a daily Discord briefing. It currently includes market prices and Daily Firehose RSS article updates. The user wants to add a new **top 5 news headlines** section. The section should include news from a variety of sources across the US political spectrum and the world. Each headline should show an icon indicating the source’s general bias/leaning: liberal, conservative, or neutral/balanced/bi-partisan. We discussed a first-pass implementation using curated RSS sources with fixed source-level bias metadata, recent headlines from roughly the last 24–30 hours, light deduping, and selection for diversity across left/center/right/international sources.

## Goals / Non-goals

- Goals:
  - Add a new modular Morning Brief section for “Top News Headlines”.
  - Select 5 recent headlines.
  - Use curated RSS feeds rather than introducing a news API/key dependency for the first pass.
  - Include sources across liberal/left-leaning, conservative/right-leaning, and neutral/wire/international categories.
  - Label each headline with an icon:
    - 🔵 liberal / left-leaning source
    - 🔴 conservative / right-leaning source
    - ⚪ neutral / center / balanced / wire / international source
  - Treat bias labels as source-level metadata, not per-article inference.
  - Favor diversity across source leanings and sources when choosing the top 5.

- Non-goals:
  - Do not attempt ML/LLM-based political bias analysis of individual articles.
  - Do not add paid news APIs or API keys in the first pass.
  - Do not replace the existing markets or Daily Firehose RSS sections.
  - Do not over-engineer story clustering beyond light title deduping for this iteration.

## Files to change

- `morning-brief/src/morning_brief/modules/news.py` — new briefing module to fetch curated news RSS feeds, parse headlines, assign source-level bias icons, dedupe/select 5 diverse headlines, and format the section.
- `morning-brief/src/morning_brief/briefing.py` — register the new news module in the default briefing module list.
- `morning-brief/src/morning_brief/config.py` — add optional configuration for headline count if needed, defaulting to 5.
- `morning-brief/.env.example` — document any optional news-related configuration if added.
- `morning-brief/README.md` — document the new Top News Headlines section, source-level icon meanings, and first-pass RSS approach.
- `morning-brief/tests/test_news.py` — add tests for feed parsing, bias icon formatting, light deduping, and diverse top-5 selection.

## Ordered steps

1. Inspect the existing Morning Brief module pattern and tests.
2. Create a new `news.py` module implementing a `TopNewsModule` compatible with the existing `BriefingModule` protocol.
3. Define a curated first-pass list of RSS sources with source-level bias metadata covering:
   - liberal / left-leaning US sources,
   - conservative / right-leaning US sources,
   - neutral/wire/international sources.
4. Implement RSS/Atom fetching and parsing using existing project dependencies where practical.
5. Filter headlines to recent items from roughly the last 24–30 hours when publication dates are available.
6. Add light title normalization/deduping so repeated or near-identical titles are not selected twice.
7. Implement selection logic that returns up to 5 headlines while trying to include multiple bias/source categories.
8. Format the section as Discord-friendly Markdown with the icon, linked headline, source name, and short source-level bias label.
9. Register the news module in `default_modules()` so it appears in the daily briefing alongside markets and Daily Firehose RSS updates.
10. Add tests for the new module’s parsing, formatting, deduping, and selection behavior.
11. Update README and `.env.example` only for configuration/documentation actually introduced.
12. Run validation and fix any failures.
13. Commit and push the changes, then deploy to the `daily-firehose` VM if implementation is requested after this finalized plan.

## Validation

- `cd /home/feoh/src/personal/morning-brief && uv run pytest`
- `cd /home/feoh/src/personal/morning-brief && uv run mypy src/morning_brief tests`
- `cd /home/feoh/src/personal/morning-brief && uv run pre-commit run --files $(git ls-files --modified --others --exclude-standard)`
- `cd /home/feoh/src/personal/morning-brief && uv run morning-brief preview` to confirm the new Top News Headlines section renders.
- After deployment, run `uv run morning-brief preview` and optionally `uv run morning-brief run` on the `daily-firehose` VM to confirm Discord output.
- Confirm the existing systemd timer remains enabled with `systemctl --user status morning-brief.timer` on the VM.

## Risks & unknowns

- RSS feed availability and formats vary by publisher; some feeds may fail or omit dates.
- “Top” is approximate in the first pass: it will mean recent, diverse headlines from curated feeds rather than a globally ranked news agenda.
- Source-level bias labels are simplifications and may need adjustment as the source list evolves.
- Dedupe will be light and title-based; different wording for the same story may still appear more than once.
- Exact source list was not finalized beyond the desired categories, so the first implementation should choose reasonable curated defaults and make them easy to revise.
