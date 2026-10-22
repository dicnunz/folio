from pathlib import Path
from streamlit.testing.v1 import AppTest

from folio.application import open_application
from scripts.seed_academic_fixture import seed

APP = Path(__file__).resolve().parents[1] / 'app.py'


def field(app, label):
    return next(element for element in app.text_input if element.label == label)


def click(app, label):
    return next(element for element in app.button if element.label == label).click().run()


def test_coursework_controls_restore_and_edit(tmp_path, monkeypatch):
    path = tmp_path / 'app.sqlite3'
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception
    click(app, 'Save coursework')
    assert len(app.error) == 3
    for label, value in [('Course','CSE491'), ('Assignment name','Original'), ('Due date (YYYY-MM-DD)','2026-10-26')]:
        field(app, label).set_value(value)
    click(app, 'Save coursework')
    assert app.success[0].value == 'Coursework saved.'
    field(app, 'Edit assignment name').set_value('Edited')
    click(app, 'Save changes')
    assert app.success[0].value == 'Coursework changes saved.'
    field(app, 'Edit course').set_value('')
    click(app, 'Save changes')
    assert app.error
    restart = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not restart.exception
    assert field(restart, 'Edit assignment name').value == 'Edited'
    assert field(restart, 'Edit course').value == 'CSE491'
    click(restart, 'Delete selected coursework')
    assert open_application(path)[0].restore_saved_application_state()['coursework'] == []


def test_plan_fixture_display_and_dependent_delete(tmp_path, monkeypatch):
    path = tmp_path / 'fixture.sqlite3'
    seed(path)
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    click(app, 'Open saved plan')
    assert not app.exception
    assert any(heading.value == 'Plan A' for heading in app.subheader)
    assert len(app.dataframe) == 4  # coursework, selected tasks, feedback, all tasks
    click(app, 'Delete selected coursework')
    assert any('referenced' in error.value for error in app.error)


def test_storage_startup_failure_is_visible(tmp_path, monkeypatch):
    path = tmp_path / 'invalid.sqlite3'
    path.write_text('not a SQLite database')
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert not app.exception and app.error
    assert 'storage' in app.error[0].value


def test_manual_times_saved_and_restored(tmp_path, monkeypatch):
    monkeypatch.setenv('FOLIO_DATABASE', str(tmp_path / 'times.sqlite3'))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    for label, value in [('Course','CSE491'), ('Assignment name','Exam'),
                         ('Due date (YYYY-MM-DD)','2026-10-26'),
                         ('Start time (optional, YYYY-MM-DDTHH:MM)','2026-10-26T09:00'),
                         ('End time (optional, YYYY-MM-DDTHH:MM)','2026-10-26T10:00')]:
        field(app, label).set_value(value)
    click(app, 'Save coursework')
    assert not app.exception and app.success
    field(app, 'Edit end time (YYYY-MM-DDTHH:MM)').set_value('2026-10-26T08:00')
    click(app, 'Save changes')
    assert app.error
    restart = AppTest.from_file(str(APP), default_timeout=15).run()
    assert field(restart, 'Edit start time (YYYY-MM-DDTHH:MM)').value == '2026-10-26T09:00'
    assert field(restart, 'Edit end time (YYYY-MM-DDTHH:MM)').value == '2026-10-26T10:00'
