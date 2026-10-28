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
    for label, value in [('Course','CSE491'), ('Coursework name','Original'), ('Due date','2026-10-26')]:
        field(app, label).set_value(value)
    click(app, 'Save coursework')
    assert app.success[0].value == 'Coursework saved.'
    app.selectbox(key='coursework_picker').set_value(1).run()
    field(app, 'Coursework name').set_value('Edited')
    click(app, 'Save changes')
    assert app.success[0].value == 'Changes saved.'
    field(app, 'Course').set_value('')
    click(app, 'Save changes')
    assert app.error
    restart = AppTest.from_file(str(APP), default_timeout=15).run()
    restart.selectbox(key='coursework_picker').set_value(1).run()
    assert not restart.exception
    assert field(restart, 'Coursework name').value == 'Edited'
    assert field(restart, 'Course').value == 'CSE491'
    restart.checkbox[0].check().run()
    click(restart, 'Delete coursework')
    assert open_application(path)[0].restore_saved_application_state()['coursework'] == []


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
    for label, value in [('Course','CSE491'), ('Coursework name','Exam'),
                         ('Due date','2026-10-26'),
                         ('Start time (optional, YYYY-MM-DDTHH:MM)','2026-10-26T09:00'),
                         ('End time (optional, YYYY-MM-DDTHH:MM)','2026-10-26T10:00')]:
        field(app, label).set_value(value)
    click(app, 'Save coursework')
    assert not app.exception and app.success
    app.selectbox(key='coursework_picker').set_value(1).run()
    field(app, 'End time (optional, YYYY-MM-DDTHH:MM)').set_value('2026-10-26T08:00')
    click(app, 'Save changes')
    assert app.error
    restart = AppTest.from_file(str(APP), default_timeout=15).run()
    restart.selectbox(key='coursework_picker').set_value(1).run()
    assert field(restart, 'Start time (optional, YYYY-MM-DDTHH:MM)').value == '2026-10-26T09:00'
    assert field(restart, 'End time (optional, YYYY-MM-DDTHH:MM)').value == '2026-10-26T10:00'
