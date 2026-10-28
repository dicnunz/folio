"""Real app acceptance checks for the overdue coursework/planning handoff."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from folio.application import open_application

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_coursework_uses_real_relationships_and_hands_selection_to_plan(tmp_path, monkeypatch):
    path = tmp_path / 'academic.sqlite3'
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    repository, service = open_application(path)
    row = service.create_coursework({'course': 'CSE 4101', 'item_name': 'M2 assignment', 'due_date': '2026-10-26'})['record']
    app = AppTest.from_file(str(APP)).run()
    app.selectbox(key='coursework_picker').set_value(row['id']).run()
    next(x for x in app.button if x.label == 'Use for planning').click().run()
    assert app.session_state['planning_coursework_id'] == row['id']
    app.radio(key='folio_screen').set_value('Plan').run()
    assert not app.exception
    assert any(x.value == 'Plan' for x in app.title)


def test_real_repository_refuses_referenced_deletion(tmp_path, monkeypatch):
    path = tmp_path / 'academic.sqlite3'
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    repository, service = open_application(path)
    row = service.create_coursework({'course': 'CSE', 'item_name': 'Exam', 'due_date': '2026-10-26'})['record']
    repository.store_plan_data({'coursework_id': row['id'], 'name': 'Exam preparation'})
    app = AppTest.from_file(str(APP)).run()
    app.selectbox(key='coursework_picker').set_value(row['id']).run()
    next(x for x in app.checkbox if x.label == 'Confirm deletion of this coursework').check().run()
    next(x for x in app.button if x.label == 'Delete coursework').click().run()
    assert any('referenced' in x.value for x in app.error)
    assert len(repository.restore_saved_application_state()['coursework']) == 1
