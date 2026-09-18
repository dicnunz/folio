from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

try:
    from apscheduler.triggers.interval import IntervalTrigger
except Exception:  # pragma: no cover
    IntervalTrigger = None

try:
    import schedule  # type: ignore
except Exception:  # pragma: no cover
    schedule = None


CANDIDATE_METADATA = {
    "stdlib": {
        "dependencies": [],
        "setup": "No extra install required; use Python 3.11+ standard library only.",
        "approx_code": "Small custom module with datetime + zoneinfo logic.",
        "recurring": "Manual implementation required.",
        "timezone": "Built in via zoneinfo and datetime.astimezone().",
        "next_run": "Straightforward with custom recurrence arithmetic.",
        "complexity": "Low to medium.",
        "maintainability": "High when logic remains small and explicit.",
        "limitations": "No native recurring-task abstraction; all recurrence rules are custom.",
        "scale_fit": "Good fit for Folio's expected task-planning scale.",
    },
    "apscheduler": {
        "dependencies": ["APScheduler"],
        "setup": "python -m pip install APScheduler",
        "approx_code": "Small adapter around interval triggers and task metadata.",
        "recurring": "Built in for repeated jobs with interval triggers.",
        "timezone": "Supported through trigger timezone and timezone-aware datetimes.",
        "next_run": "Good for job scheduling, but more than Folio needs for plain planning.",
        "complexity": "Medium.",
        "maintainability": "Moderate; broad API with more execution semantics than planning logic.",
        "limitations": "Background-job oriented; not a task-planning domain model by itself.",
        "scale_fit": "Appropriate for background job execution, not ideal for core Folio planning logic.",
    },
    "schedule": {
        "dependencies": ["schedule"],
        "setup": "python -m pip install schedule",
        "approx_code": "Small adapter; recurring logic still mostly custom around job metadata.",
        "recurring": "Recurring job registration exists, but planning next-run times is not a first-class abstraction.",
        "timezone": "Usually requires manual handling for explicit time zones.",
        "next_run": "Not natural for arbitrary planning queries; custom logic is usually needed.",
        "complexity": "Medium.",
        "maintainability": "Low to moderate; embedded in background-job execution semantics.",
        "limitations": "Primarily for running background jobs, not general task planning or calendar logic.",
        "scale_fit": "Not a strong fit for Folio's planning core unless extended with custom logic.",
    },
}


def normalize_datetime(value, *, default_tz=None):
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - exercised via tests
            raise ValueError(f"Invalid datetime value: {value!r}") from exc
    else:
        raise TypeError(f"Expected datetime or ISO-8601 string, got {type(value).__name__}")

    if dt.tzinfo is None and default_tz is not None:
        dt = dt.replace(tzinfo=default_tz)
    if dt.tzinfo is not None and default_tz is not None:
        dt = dt.astimezone(default_tz)
    return dt


def due_status(due_at: datetime, now: datetime) -> str:
    if due_at < now:
        return "overdue"
    if due_at.date() == now.date():
        return "due today"
    return "upcoming"


@dataclass(frozen=True)
class StdLibTask:
    title: str
    due_at: datetime


@dataclass(frozen=True)
class StdLibRecurringTask:
    title: str
    start: datetime
    interval: str


class StdLibPlanner:
    @staticmethod
    def make_task(title: str, due_at):
        dt = normalize_datetime(due_at, default_tz=ZoneInfo("UTC"))
        return StdLibTask(title=title, due_at=dt)

    @staticmethod
    def classify(task: StdLibTask, now):
        now_dt = normalize_datetime(now, default_tz=ZoneInfo("UTC"))
        return due_status(task.due_at, now_dt)

    @staticmethod
    def sort_tasks(tasks):
        return sorted(tasks, key=lambda task: task.due_at)

    @staticmethod
    def make_recurring_task(title: str, start, interval: str):
        if interval not in {"daily", "weekly"}:
            raise ValueError(f"Unsupported interval: {interval!r}")
        start_dt = normalize_datetime(start, default_tz=ZoneInfo("UTC"))
        return StdLibRecurringTask(title=title, start=start_dt, interval=interval)

    @staticmethod
    def next_occurrence(task: StdLibRecurringTask, after):
        after_dt = normalize_datetime(after, default_tz=ZoneInfo("UTC"))
        delta = timedelta(days=1) if task.interval == "daily" else timedelta(weeks=1)
        candidate = task.start
        while candidate <= after_dt:
            candidate += delta
        return candidate


class APSchedulerPlanner:
    def __init__(self):
        if IntervalTrigger is None:
            raise RuntimeError("APScheduler is not installed")

    @staticmethod
    def make_task(title: str, due_at):
        dt = normalize_datetime(due_at, default_tz=ZoneInfo("UTC"))
        return {"title": title, "due_at": dt}

    @staticmethod
    def classify(task, now):
        now_dt = normalize_datetime(now, default_tz=ZoneInfo("UTC"))
        return due_status(task["due_at"], now_dt)

    @staticmethod
    def sort_tasks(tasks):
        return sorted(tasks, key=lambda task: task["due_at"])

    @staticmethod
    def make_recurring_task(title: str, start, interval: str):
        if interval not in {"daily", "weekly"}:
            raise ValueError(f"Unsupported interval: {interval!r}")
        start_dt = normalize_datetime(start, default_tz=ZoneInfo("UTC"))
        kwargs = {"start_date": start_dt, "timezone": start_dt.tzinfo}
        if interval == "daily":
            trigger = IntervalTrigger(days=1, **kwargs)
        else:
            trigger = IntervalTrigger(weeks=1, **kwargs)
        return {"title": title, "start": start_dt, "interval": interval, "trigger": trigger}

    @staticmethod
    def next_occurrence(task, after):
        after_dt = normalize_datetime(after, default_tz=ZoneInfo("UTC"))
        trigger = task["trigger"]
        # APScheduler's get_next_fire_time() is inclusive of the current scheduled run
        # when `after` lands exactly on a trigger boundary, while task-planning code
        # usually wants the first occurrence strictly after the reference moment.
        candidate = after_dt + timedelta(microseconds=1)
        return trigger.get_next_fire_time(None, candidate)


class SchedulePlanner:
    def __init__(self):
        if schedule is None:
            raise RuntimeError("schedule is not installed")

    @staticmethod
    def make_task(title: str, due_at):
        dt = normalize_datetime(due_at, default_tz=ZoneInfo("UTC"))
        return {"title": title, "due_at": dt}

    @staticmethod
    def classify(task, now):
        now_dt = normalize_datetime(now, default_tz=ZoneInfo("UTC"))
        return due_status(task["due_at"], now_dt)

    @staticmethod
    def sort_tasks(tasks):
        return sorted(tasks, key=lambda task: task["due_at"])

    @staticmethod
    def make_recurring_task(title: str, start, interval: str):
        if interval not in {"daily", "weekly"}:
            raise ValueError(f"Unsupported interval: {interval!r}")
        start_dt = normalize_datetime(start, default_tz=ZoneInfo("UTC"))
        return {"title": title, "start": start_dt, "interval": interval, "job_metadata": True}

    @staticmethod
    def next_occurrence(task, after):
        after_dt = normalize_datetime(after, default_tz=ZoneInfo("UTC"))
        start_dt = task["start"]
        delta = timedelta(days=1) if task["interval"] == "daily" else timedelta(weeks=1)
        candidate = start_dt
        while candidate <= after_dt:
            candidate += delta
        return candidate


PLANNERS = [StdLibPlanner, APSchedulerPlanner, SchedulePlanner]


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_one_future_task(planner_cls):
    planner = planner_cls()
    task = planner.make_task("Future task", "2025-01-16T09:00:00+00:00")
    assert planner.classify(task, "2025-01-15T09:00:00+00:00") == "upcoming"


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_one_task_due_today(planner_cls):
    planner = planner_cls()
    task = planner.make_task("Due today", "2025-01-15T17:30:00+00:00")
    assert planner.classify(task, "2025-01-15T09:00:00+00:00") == "due today"


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_one_overdue_task(planner_cls):
    planner = planner_cls()
    task = planner.make_task("Overdue task", "2025-01-14T09:00:00+00:00")
    assert planner.classify(task, "2025-01-15T09:00:00+00:00") == "overdue"


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_three_tasks_sorted_chronologically(planner_cls):
    planner = planner_cls()
    tasks = [
        planner.make_task("Late", "2025-01-16T12:00:00+00:00"),
        planner.make_task("Soon", "2025-01-15T08:00:00+00:00"),
        planner.make_task("Now", "2025-01-15T09:00:00+00:00"),
    ]
    ordered = planner.sort_tasks(tasks)
    # Each candidate stores task data in a different representation; normalize that before comparing.
    ordered_titles = [task["title"] if isinstance(task, dict) else task.title for task in ordered]
    assert ordered_titles == ["Soon", "Now", "Late"]


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_daily_recurring_task(planner_cls):
    planner = planner_cls()
    task = planner.make_recurring_task("Daily standup", "2025-01-15T09:00:00+00:00", "daily")
    assert planner.next_occurrence(task, "2025-01-15T09:00:00+00:00") == datetime(2025, 1, 16, 9, 0, tzinfo=ZoneInfo("UTC"))


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_weekly_recurring_task(planner_cls):
    planner = planner_cls()
    task = planner.make_recurring_task("Weekly review", "2025-01-15T09:00:00+00:00", "weekly")
    assert planner.next_occurrence(task, "2025-01-15T09:00:00+00:00") == datetime(2025, 1, 22, 9, 0, tzinfo=ZoneInfo("UTC"))


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_next_occurrence_after_a_previous_run(planner_cls):
    planner = planner_cls()
    task = planner.make_recurring_task("Daily task", "2025-01-15T09:00:00+00:00", "daily")
    assert planner.next_occurrence(task, "2025-01-17T10:00:00+00:00") == datetime(2025, 1, 18, 9, 0, tzinfo=ZoneInfo("UTC"))


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_timezone_aware_task_comparison(planner_cls):
    planner = planner_cls()
    tasks = [
        planner.make_task("Los Angeles", "2025-02-03T01:00:00-08:00"),
        planner.make_task("New York", "2025-02-03T04:00:00-05:00"),
        planner.make_task("UTC", "2025-02-03T09:00:00+00:00"),
    ]
    ordered = planner.sort_tasks(tasks)
    ordered_titles = [task["title"] if isinstance(task, dict) else task.title for task in ordered]
    assert ordered_titles == ["Los Angeles", "New York", "UTC"]


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_invalid_datetime_input(planner_cls):
    planner = planner_cls()
    with pytest.raises((TypeError, ValueError)):
        planner.make_task("Broken", "not-a-date")


@pytest.mark.parametrize("planner_cls", PLANNERS)
def test_no_crash_during_normal_use(planner_cls):
    planner = planner_cls()
    tasks = [
        planner.make_task("T1", "2025-02-01T09:00:00+00:00"),
        planner.make_task("T2", "2025-02-02T09:00:00+00:00"),
        planner.make_task("T3", "2025-02-03T09:00:00+00:00"),
    ]
    result = planner.sort_tasks(tasks)
    statuses = [planner.classify(task, "2025-02-02T12:00:00+00:00") for task in result]
    assert statuses[0] in {"upcoming", "due today", "overdue"}
    assert statuses[1] in {"upcoming", "due today", "overdue"}
    assert statuses[2] in {"upcoming", "due today", "overdue"}


def test_metadata_documents_library_fit_for_task_planning():
    assert "stdlib" in CANDIDATE_METADATA
    assert "apscheduler" in CANDIDATE_METADATA
    assert "schedule" in CANDIDATE_METADATA
    assert CANDIDATE_METADATA["apscheduler"]["limitations"]
    assert CANDIDATE_METADATA["schedule"]["limitations"]
