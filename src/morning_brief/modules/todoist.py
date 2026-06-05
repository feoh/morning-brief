"""Todoist task briefing module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import requests

from .base import BriefSection

TODOIST_TASKS_URL = "https://api.todoist.com/api/v1/tasks"


@dataclass(frozen=True)
class TodoistDue:
    """Due date metadata for a Todoist task."""

    date_value: date
    datetime_value: datetime | None = None


@dataclass(frozen=True)
class TodoistTask:
    """One active Todoist task with a due date."""

    task_id: str
    content: str
    due: TodoistDue
    url: str | None = None
    priority: int = 1


class TodoistModule:
    """Build a briefing section containing overdue and upcoming Todoist tasks."""

    name = "todoist"

    def __init__(
        self,
        api_token: str | None,
        task_limit: int = 20,
        timezone: str = "America/New_York",
    ) -> None:
        self.api_token = api_token
        self.task_limit = task_limit
        self.timezone = timezone

    def build_section(self) -> BriefSection:
        """Build the Todoist tasks section."""

        if not self.api_token:
            return BriefSection(
                title="Todoist Tasks",
                body="Todoist API token is not configured.",
            )

        try:
            tasks = fetch_todoist_tasks(
                api_token=self.api_token,
                task_limit=self.task_limit,
                timezone=self.timezone,
            )
        except requests.RequestException as exc:
            return BriefSection(
                title="Todoist Tasks",
                body=f"Todoist API request failed: {exc}",
            )
        except (KeyError, TypeError, ValueError) as exc:
            return BriefSection(
                title="Todoist Tasks",
                body=f"Todoist API response could not be parsed: {exc}",
            )

        return BriefSection(title="Todoist Tasks", body=format_todoist_tasks(tasks))


def fetch_todoist_tasks(
    *, api_token: str, task_limit: int, timezone: str = "America/New_York"
) -> list[TodoistTask]:
    """Fetch active Todoist tasks due within the next week or overdue."""

    local_tz = ZoneInfo(timezone)
    now = datetime.now(local_tz)
    today = now.date()
    horizon = today + timedelta(days=7)

    payload = _fetch_all_task_payloads(api_token)
    tasks = [
        _task_from_payload(raw_task, local_tz=local_tz)
        for raw_task in payload
        if raw_task.get("due")
        and not raw_task.get("checked", False)
        and not raw_task.get("is_deleted", False)
    ]
    due_tasks = [
        task for task in tasks if _is_due_by_horizon(task, now=now, horizon=horizon)
    ]
    return sorted(due_tasks, key=_task_sort_key)[:task_limit]


def _fetch_all_task_payloads(api_token: str) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        params = {"cursor": cursor} if cursor else None
        response = requests.get(
            TODOIST_TASKS_URL,
            headers={"Authorization": f"Bearer {api_token}"},
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            tasks.extend(payload)
            return tasks
        tasks.extend(payload["results"])
        cursor = payload.get("next_cursor")
        if not cursor:
            return tasks


def _task_from_payload(payload: dict[str, Any], *, local_tz: ZoneInfo) -> TodoistTask:
    due_payload = payload["due"]
    return TodoistTask(
        task_id=str(payload["id"]),
        content=str(payload["content"]),
        due=_due_from_payload(due_payload, local_tz=local_tz),
        url=payload.get("url"),
        priority=int(payload.get("priority", 1)),
    )


def _due_from_payload(payload: dict[str, Any], *, local_tz: ZoneInfo) -> TodoistDue:
    datetime_value = _parse_due_datetime(payload.get("datetime"))
    if datetime_value is not None:
        datetime_value = datetime_value.astimezone(local_tz)
    date_value = _parse_due_date(str(payload["date"]))
    return TodoistDue(date_value=date_value, datetime_value=datetime_value)


def _parse_due_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def _parse_due_date(value: str) -> date:
    return date.fromisoformat(value[:10])


def _is_due_by_horizon(task: TodoistTask, *, now: datetime, horizon: date) -> bool:
    if task.due.datetime_value is not None:
        return task.due.datetime_value.date() <= horizon
    return task.due.date_value <= horizon


def _task_sort_key(task: TodoistTask) -> tuple[date, time, int, str]:
    due_time = time.min
    if task.due.datetime_value is not None:
        due_time = task.due.datetime_value.timetz().replace(tzinfo=None)
    # Todoist priority 4 is highest, so sort descending by negating it.
    return (task.due.date_value, due_time, -task.priority, task.content.lower())


def format_todoist_tasks(tasks: list[TodoistTask]) -> str:
    """Format Todoist tasks as Discord-friendly Markdown."""

    if not tasks:
        return "No Todoist tasks are overdue or due within the next week."

    lines = [f"_As of {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}_", ""]
    today = datetime.now().date()
    for task in tasks:
        due_label = _format_due_label(task.due, today=today)
        title = f"[{task.content}]({task.url})" if task.url else task.content
        priority = f" · P{task.priority}" if task.priority > 1 else ""
        lines.append(f"- **{due_label}** — {title}{priority}")
    return "\n".join(lines)


def _format_due_label(due: TodoistDue, *, today: date) -> str:
    if due.date_value < today:
        prefix = f"Overdue ({due.date_value.isoformat()})"
    elif due.date_value == today:
        prefix = "Today"
    elif due.date_value == today + timedelta(days=1):
        prefix = "Tomorrow"
    else:
        prefix = due.date_value.isoformat()

    if due.datetime_value is None:
        return prefix
    return f"{prefix} {due.datetime_value.strftime('%H:%M')}"
