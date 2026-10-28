from pathlib import Path

from streamlit.testing.v1 import AppTest

from folio.storage import AcademicRepository

APP = Path(__file__).resolve().parents[1] / "cloud_app.py"


def test_password_gate_masks_input_and_blocks_wrong_password(monkeypatch):
    monkeypatch.setenv("FOLIO_DEMO_PASSWORD", "test-secret")
    app = AppTest.from_file(str(APP)).run()
    assert not app.exception
    assert app.title[0].value == "Folio v0.5"
    assert app.text_input[0].label == "Demo password"
    assert app.text_input[0].proto.type == app.text_input[0].proto.PASSWORD
    assert not app.radio
    app.text_input[0].set_value("wrong")
    app.button[0].click().run()
    assert app.error[0].value == "Incorrect password."
    assert not app.radio
    assert not app.session_state["demo_authenticated"]


def test_shared_demo_reopens_saved_data_after_new_session(tmp_path, monkeypatch):
    monkeypatch.setenv("FOLIO_DEMO_PASSWORD", "test-secret")
    for key in ("FOLIO_SUPABASE_URL", "FOLIO_SUPABASE_KEY", "FOLIO_STORAGE_TOKEN"):
        monkeypatch.setenv(key, "test-config")
    path = tmp_path / "shared.sqlite3"
    monkeypatch.setattr("folio.cloud_storage.CloudAcademicRepository", lambda *args: AcademicRepository(path))

    def login():
        app = AppTest.from_file(str(APP)).run()
        assert not app.radio
        app.text_input[0].set_value("test-secret")
        app.button[0].click().run()
        assert not app.exception
        assert app.session_state["demo_authenticated"]
        assert "demo_password" not in app.session_state
        return app

    first = login()
    for label, value in [("Course", "CS"), ("Coursework name", "Saved demo"), ("Due date", "2026-11-23")]:
        next(widget for widget in first.text_input if widget.label == label).set_value(value)
    next(button for button in first.button if button.label == "Save coursework").click().run()
    assert first.success and not first.exception
    second = login()
    assert second.dataframe[0].value.iloc[0]["Coursework name"] == "Saved demo"
    assert "remain after you leave" in second.sidebar.caption[0].value


def test_unconfigured_password_fails_closed(monkeypatch):
    monkeypatch.setenv("FOLIO_DEMO_PASSWORD", "")
    app = AppTest.from_file(str(APP)).run()
    assert app.error[0].value == "Demo access is not configured."
    assert not app.radio and not app.button
