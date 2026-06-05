from __future__ import annotations

from datetime import datetime, timedelta
from importlib import import_module
from typing import Any
from zoneinfo import ZoneInfo


class FakeResponse:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> list[dict[str, Any]]:
        return self.payload


def _todoist() -> Any:
    return import_module("morning_brief.modules.todoist")


def test_fetch_todoist_tasks_filters_and_sorts_due_tasks(monkeypatch: Any) -> None:
    todoist = _todoist()
    today = datetime.now(ZoneInfo("America/New_York")).date()
    payload = [
        {
            "id": "1",
            "content": "Future outside horizon",
            "due": {"date": (today + timedelta(days=8)).isoformat()},
            "priority": 1,
            "url": "https://todoist.com/task/1",
        },
        {
            "id": "2",
            "content": "Overdue task",
            "due": {"date": (today - timedelta(days=1)).isoformat()},
            "priority": 1,
            "url": "https://todoist.com/task/2",
        },
        {
            "id": "3",
            "content": "Upcoming task",
            "due": {"date": (today + timedelta(days=2)).isoformat()},
            "priority": 4,
            "url": "https://todoist.com/task/3",
        },
        {"id": "4", "content": "Undated task", "priority": 1},
    ]

    def fake_get(*args: Any, **kwargs: Any) -> FakeResponse:
        assert kwargs["headers"] == {"Authorization": "Bearer test-token"}
        return FakeResponse(payload)

    monkeypatch.setattr(todoist.requests, "get", fake_get)

    tasks = todoist.fetch_todoist_tasks(api_token="test-token", task_limit=10)

    assert [task.content for task in tasks] == ["Overdue task", "Upcoming task"]


def test_format_todoist_tasks_includes_links_and_priorities() -> None:
    todoist = _todoist()
    today = datetime.now().date()
    tasks = [
        todoist.TodoistTask(
            task_id="1",
            content="Pay bills",
            due=todoist.TodoistDue(today),
            url="https://todoist.com/task/1",
            priority=4,
        )
    ]

    output = todoist.format_todoist_tasks(tasks)

    assert "**Today**" in output
    assert "[Pay bills](https://todoist.com/task/1)" in output
    assert "P4" in output


def test_format_todoist_tasks_handles_empty_list() -> None:
    todoist = _todoist()

    assert (
        todoist.format_todoist_tasks([])
        == "No Todoist tasks are overdue or due within the next week."
    )
