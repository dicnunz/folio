from pathlib import Path

from streamlit.testing.v1 import AppTest

from folio.application import open_application

APP = Path(__file__).resolve().parents[1] / "cloud_app.py"


def test_public_demo_sessions_are_isolated_and_reruns_keep_work(tmp_path, monkeypatch):
    shared_path = tmp_path / "shared.sqlite3"
    monkeypatch.setenv("FOLIO_DATABASE", str(shared_path))
    first = AppTest.from_file(str(APP), default_timeout=15).run()
    second = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not first.exception and not second.exception
    first_directory = first.session_state["_folio_demo_directory"]
    second_directory = second.session_state["_folio_demo_directory"]
    first_path = Path(first_directory.name) / "academic.sqlite3"
    second_path = Path(second_directory.name) / "academic.sqlite3"
    assert first_path != second_path
    assert not shared_path.exists()
    assert "saved only for this session" in first.sidebar.caption[0].value

    for label, value in [("Course", "CSE491"), ("Coursework name", "Private example"),
                         ("Due date", "2026-11-15")]:
        next(element for element in first.text_input if element.label == label).set_value(value)
    next(element for element in first.button if element.label == "Save coursework").click().run()
    assert not first.exception and first.success
    first.run()
    second.run()
    assert first.session_state["_folio_demo_directory"] is first_directory
    saved = open_application(first_path)[0].restore_saved_application_state()["coursework"]
    assert saved[0]["item_name"] == "Private example"
    assert open_application(second_path)[0].restore_saved_application_state()["coursework"] == []
    first_directory.cleanup()
    second_directory.cleanup()
    assert not first_path.parent.exists() and not second_path.parent.exists()
