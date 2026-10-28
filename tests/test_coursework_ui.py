"""Real service/SQLite UI checks; upload display uses a harness, not browser proof."""
import io
import sqlite3
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from demos.src.coursework_service import CourseworkService
from folio.application import open_application

def get_all_records(database):
    return open_application(database)[0].restore_saved_application_state()["coursework"]

def SQLiteCourseworkRepository(database):
    return open_application(database)[0]

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def database(tmp_path, monkeypatch):
    path = tmp_path / "coursework.sqlite3"
    monkeypatch.setenv("FOLIO_DATABASE", str(path))
    return path


def launch():
    app = AppTest.from_file(str(ROOT / "app.py")).run()
    assert not app.exception
    return app


def button(app, label):
    return next(widget for widget in app.button if widget.label == label)


def fill(app, course="CSE", name="Essay", due="2026-10-25", score=""):
    for widget, value in zip(app.text_input, (course, name, due, score)):
        widget.set_value(value)
    return app


def save(app):
    next(widget for widget in app.button if widget.label.startswith("Save")).click().run()
    assert not app.exception


def seed(database, **changes):
    service = CourseworkService(SQLiteCourseworkRepository(database))
    data = {"course": "CSE", "item_name": "Essay", "due_date": "2026-10-25", "score": None}
    result = service.create_coursework({**data, **changes})
    assert result["success"]
    return result["record"]


def test_create_edit_optional_score_reopens(database):
    app = launch()
    save(fill(app))
    record = get_all_records(database)[0]
    assert record["score"] is None
    reopened = launch()
    reopened.selectbox(key="coursework_picker").set_value(record["id"]).run()
    assert [x.value for x in reopened.text_input] == ["CSE", "Essay", "2026-10-25", "", "", ""]
    save(fill(reopened, name="Revised", score="125.5"))
    assert get_all_records(database)[0] == {**record, "item_name": "Revised", "score": 125.5}
    again = launch()
    again.selectbox(key="coursework_picker").set_value(record["id"]).run()
    assert again.text_input[1].value == "Revised"


def test_multi_errors_and_invalid_edit_preserve_saved_record(database):
    original = seed(database)
    app = launch()
    save(fill(app, course=" ", name="", due="2026-02-30", score="nan"))
    assert len(app.error) == 4
    assert get_all_records(database) == [original]
    app.selectbox(key="coursework_picker").set_value(original["id"]).run()
    save(fill(app, course="", name="", due="bad", score="oops"))
    assert len(app.error) == 4
    assert get_all_records(database) == [original]


def test_duplicate_save_rejected(database):
    original = seed(database)
    app = launch()
    save(fill(app, score="9"))
    assert "identical required fields" in app.error[0].value
    assert get_all_records(database) == [original]


def test_selection_uses_ids_and_planning_refreshes_after_edit(database):
    first = seed(database)
    second = seed(database, course="MAT")
    app = launch()
    app.selectbox(key="coursework_picker").set_value(second["id"]).run()
    button(app, "Use for planning").click().run()
    assert app.session_state["planning_coursework_id"] == second["id"]
    assert app.session_state["planning_coursework"]["course"] == "MAT"
    save(fill(app, course="MAT", name="Revised"))
    assert app.session_state["planning_coursework"]["item_name"] == "Revised"
    assert app.selectbox(key="coursework_picker").value == second["id"]
    assert app.session_state["selected_coursework_id"] == second["id"]
    assert app.text_input[1].value == "Revised"
    assert button(app, "Save changes")
    assert get_all_records(database)[0] == first


def test_real_relationship_check_allows_unreferenced_deletion(database):
    original = seed(database)
    app = launch()
    app.selectbox(key="coursework_picker").set_value(original["id"]).run()
    assert button(app, "Delete coursework").disabled
    app.checkbox[0].check().run()
    button(app, "Delete coursework").click().run()
    assert not app.error
    assert get_all_records(database) == []


def test_stale_selected_and_planning_ids_are_cleared(database):
    record = seed(database)
    app = launch()
    app.selectbox(key="coursework_picker").set_value(record["id"]).run()
    button(app, "Use for planning").click().run()
    # Simulate external removal of unreferenced coursework.
    with sqlite3.connect(database) as connection:
        connection.execute("DELETE FROM coursework WHERE id=?", (record["id"],))
    app.run()
    assert not app.exception
    assert app.selectbox(key="coursework_picker").value is None
    assert "planning_coursework_id" not in app.session_state
    assert len(app.warning) == 2


def test_csv_service_results_render_counts_and_all_row_errors(database):
    service = CourseworkService(SQLiteCourseworkRepository(database))
    result = service.import_coursework_csv(io.StringIO(
        'course,item_name,due_date,score\nCSE,"Essay, part 1",2026-10-25,\n'
        'MAT,Exam,2026-10-26,90\nPHY,Lab,2026-10-27,\n'
        ',Missing course,2026-10-28,\nCSE,,wrong,nope\n'), source="mixed.csv")
    app = AppTest.from_string("from folio_ui.coursework import show_import_result\nimport streamlit as st\nshow_import_result(st.session_state['result'])")
    app.session_state["result"] = result
    app.run()
    assert not app.exception
    assert any("Accepted: 3 · Rejected: 2" in x.value for x in app.markdown)
    assert len(app.error) == 4
    assert all("mixed.csv · Row " in x.value for x in app.error)
    assert any("Row 5" in x.value for x in app.error)
    assert any("Row 6" in x.value for x in app.error)
    assert len(get_all_records(database)) == 3


@pytest.mark.parametrize("csv_text,expected_error,expected_info", [
    ("wrong\nx\n", "missing required columns", False),
    ('course,item_name,due_date\nCSE,"unclosed,2026-10-25\n', "unexpected end", False),
    ("", "missing required columns", False),
    ("course,item_name,due_date\n", None, True),
])
def test_csv_file_errors_and_empty_results_display_without_mutation(database, csv_text, expected_error, expected_info):
    original = seed(database)
    result = CourseworkService(SQLiteCourseworkRepository(database)).import_coursework_csv(io.StringIO(csv_text), source="test.csv")
    app = AppTest.from_string("from folio_ui.coursework import show_import_result\nimport streamlit as st\nshow_import_result(st.session_state['result'])")
    app.session_state["result"] = result
    app.run()
    assert not app.exception
    if expected_error:
        assert expected_error in app.error[0].value
    assert bool(app.info) == expected_info
    assert get_all_records(database) == [original]


def test_duplicate_import_count_display(database):
    result = CourseworkService(SQLiteCourseworkRepository(database)).import_coursework_csv(io.StringIO(
        "course,item_name,due_date,score\nCSE,Essay,2026-10-25,2\n"
        "CSE,Essay,2026-10-25,4\nCSE,Exam,2026-10-25,\n"), source="duplicates.csv")
    app = AppTest.from_string("from folio_ui.coursework import show_import_result\nimport streamlit as st\nshow_import_result(st.session_state['result'])")
    app.session_state["result"] = result
    app.run()
    assert not app.exception
    assert any("Accepted: 2 · Rejected: 1" in x.value for x in app.markdown)
    assert any("Duplicates: 1" in x.value for x in app.caption)
    assert "Row 3" in app.error[0].value
    assert len(get_all_records(database)) == 2


def test_storage_failure_display_preserves_original(database):
    original = seed(database)
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TRIGGER block_insert BEFORE INSERT ON coursework BEGIN SELECT RAISE(ABORT, 'fixture storage failure'); END")
    app = launch()
    save(fill(app, name="Second"))
    assert "fixture storage failure" in app.error[0].value
    assert get_all_records(database) == [original]


def test_selection_survives_import_changing_options(database):
    original = seed(database)
    app = launch()
    app.selectbox(key="coursework_picker").set_value(original["id"]).run()
    result = CourseworkService(SQLiteCourseworkRepository(database)).import_coursework_csv(
        io.StringIO("course,item_name,due_date\nMAT,Exam,2026-10-30\n"))
    assert result["accepted_count"] == 1
    app.run()
    assert not app.exception
    assert app.selectbox(key="coursework_picker").value == original["id"]
    assert app.session_state["selected_coursework_id"] == original["id"]
    assert app.text_input[1].value == "Essay"
    assert len(app.selectbox(key="coursework_picker").options) == 3
