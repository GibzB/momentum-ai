"""Tools M1 can call while reasoning about a project."""

import json
from datetime import UTC, date, datetime

from strands import tool

from app.models.task import list_tasks

ISO_DATE = "%Y-%m-%d"


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value[:10], ISO_DATE).date()
    except (TypeError, ValueError):
        return None


def make_get_project_tasks(project_id: str):
    """Build a task-reading tool bound to a single project.

    The agent cannot pass a project id, so prompt content can never redirect the
    lookup to another project's data.
    """

    @tool
    def get_project_tasks() -> str:
        """Fetch every task for the current project: status, description, deadline.

        Returns:
            JSON list of tasks. Completed tasks include `completedAt`.
        """
        return json.dumps(list_tasks(project_id), default=str)

    return get_project_tasks


@tool
def days_until(deadline: str) -> str:
    """Compute how many days remain until an ISO date (YYYY-MM-DD).

    Negative numbers mean the deadline has already passed.

    Args:
        deadline: ISO-8601 date string.

    Returns:
        JSON with `days_remaining`, `is_overdue` and a coarse `pressure` label
        (overdue / critical / soon / comfortable / none).
    """
    parsed = _parse_date(deadline)
    if parsed is None:
        return json.dumps(
            {"days_remaining": None, "is_overdue": False, "pressure": "none"}
        )

    remaining = (parsed - datetime.now(UTC).date()).days
    if remaining < 0:
        pressure = "overdue"
    elif remaining <= 2:
        pressure = "critical"
    elif remaining <= 7:
        pressure = "soon"
    else:
        pressure = "comfortable"

    return json.dumps(
        {"days_remaining": remaining, "is_overdue": remaining < 0, "pressure": pressure}
    )


@tool
def eisenhower_quadrant(days_remaining: int | None, importance: int) -> str:
    """Map deadline pressure and importance to an Eisenhower Matrix quadrant.

    Args:
        days_remaining: Days until the task deadline, or null if none.
        importance: 1-10 rating of how much the task advances the project objective.

    Returns:
        One of urgent-important, urgent-not-important, not-urgent-important,
        not-urgent-not-important.
    """
    urgent = days_remaining is not None and days_remaining <= 7
    important = importance >= 6
    if urgent and important:
        return "urgent-important"
    if urgent:
        return "urgent-not-important"
    if important:
        return "not-urgent-important"
    return "not-urgent-not-important"
