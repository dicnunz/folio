"""Explicit, test-only fixtures for missing plan/feedback screens.

Usage from repo root: python -m scripts.seed_academic_fixture /tmp/folio-demo.sqlite3
Refuses existing files. The app itself NEVER inserts these records at startup.
"""
import sys
from pathlib import Path
from folio.application import open_application


def seed(path):
    if Path(path).exists():
        raise ValueError("Fixture destination already exists; choose a fresh temporary path.")
    repository, service = open_application(path)
    coursework = service.create_coursework({"course": "CS 491", "item_name": "Design review",
                                          "due_date": "2026-10-26"})["record"]
    for index, name in enumerate(("Plan A", "Plan B")):
        repository.StorePlanData(
            {"coursework_id": coursework["id"], "name": name, "template_id": "fixture",
             "notes": "CSE-22 test fixture for persistence verification."},
            [{"name": "Review", "start_time": f"2026-10-22T{10 + index}:00",
              "end_time": f"2026-10-22T{11 + index}:00", "completed": bool(index)},
             {"name": "Revise", "start_time": f"2026-10-23T{10 + index}:00",
              "end_time": f"2026-10-23T{11 + index}:00"}],
            [{"suggestion": "Clarify the validation examples.", "decision": "adapt",
              "adapted_text": "Add one invalid-row example."}])
    return repository.RestoreSavedApplicationState()


if __name__ == "__main__":
    state = seed(sys.argv[1])
    print({name: len(rows) for name, rows in state.items()})
