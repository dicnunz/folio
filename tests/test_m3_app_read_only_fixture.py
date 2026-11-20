from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from folio.application import open_application


APP = Path(__file__).resolve().parents[1] / "app.py"


def test_schedule_reports_saved_progress_and_enables_local_writes(tmp_path, monkeypatch):
    database = tmp_path / "read_only.sqlite3"
    monkeypatch.setenv("FOLIO_DATABASE", str(database))
    repository, service = open_application(database)
    item = service.create_coursework({
        "course": "CSE-SYNTHETIC", "item_name": "Essay", "due_date": "2026-11-23"
    })["record"]
    plan = repository.StorePlanData({"coursework_id": item["id"], "name": "Test plan"}, [
        {"name": "Read", "start_time": "2026-11-20T09:00",
         "end_time": "2026-11-20T10:00", "completed": True},
        {"name": "Outline", "start_time": "2026-11-22T09:00",
         "end_time": "2026-11-22T10:00", "completed": False},
    ])
    before = repository.RestoreSavedApplicationState()

    for _ in range(2):
        app = AppTest.from_file(str(APP), default_timeout=15).run()
        app.radio(key="folio_screen").set_value("Schedule").run()
        app.date_input(key="schedule_date").set_value(date(2026, 11, 20)).run()
        assert not app.exception
        assert len(app.table[0].value) == 1
        assert any("1 of 2 tasks complete" in block.value for block in app.markdown)
        assert any("Reminders require Folio and its browser session to remain active." in item.value for item in app.caption)
        task = app.selectbox(key="follow_through_task")
        assert task.value == plan["tasks"][0]["id"]
        buttons = {button.label: button.disabled for button in app.button}
        assert not buttons["Mark incomplete"] and not buttons["Save reminder"]
        assert not buttons["Save corrected time"]
        assert not next(widget for widget in app.checkbox if widget.label == "Enable reminder").disabled
        assert repository.RestoreSavedApplicationState() == before
