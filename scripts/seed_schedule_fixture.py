"""Explicit CSE-23 sample plans; never run automatically by the application.

python -m scripts.seed_schedule_fixture /tmp/folio-schedule.sqlite3
Use a new path. For existing coursework, tests may call add_sample_plans().
"""
from datetime import date, timedelta
from pathlib import Path
import sys

from folio.application import open_application


def add_sample_plans(repository, coursework_id, day=date(2026, 10, 26)):
    """Attach two identified fixture plans to real, already-saved coursework."""
    if repository.restore_saved_application_state()["plans"]:
        raise ValueError("Sample plans require a test database without existing plans.")
    def task(name, start, end, offset=0):
        prefix = (day + timedelta(days=offset)).isoformat()
        return {"name": name, "start_time": f"{prefix}T{start}", "end_time": f"{prefix}T{end}"}
    a = repository.StorePlanData({"coursework_id": coursework_id, "name": "Plan A", "template_id": "cse23-fixture"},
        [task("Review", "10:00", "11:00"), task("Resolve overlap", "10:30", "11:30"),
         task("Next-day review", "10:00", "11:00", 1)],
        [{"suggestion": "Fixture feedback for restoration checks."}])
    b = repository.StorePlanData({"coursework_id": coursework_id, "name": "Plan B", "template_id": "cse23-fixture"},
        [task("Review", "11:00", "12:00")], [])
    return a, b


def seed(path):
    if Path(path).exists():
        raise ValueError("Choose a new temporary database path; this file already exists.")
    repository, service = open_application(path)
    course = service.create_coursework({"course": "CS 491", "item_name": "Schedule review", "due_date": "2026-10-30"})["record"]
    add_sample_plans(repository, course["id"])
    return repository.restore_saved_application_state()


if __name__ == '__main__':
    print({key: len(rows) for key, rows in seed(sys.argv[1]).items()})
