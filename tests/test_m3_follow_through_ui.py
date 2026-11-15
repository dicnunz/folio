import pytest
from streamlit.testing.v1 import AppTest
from folio_ui.follow_through import validate_reminder
from folio.application import open_application


def setup(tmp_path):
    path = tmp_path / 'm3.sqlite3'
    repo, service = open_application(path)
    item = service.create_coursework({'course': 'C', 'item_name': 'Essay', 'due_date': '2026-11-23'})['record']
    def task(name):
        return {'name': name, 'start_time': '2026-11-20T09:00', 'end_time': '2026-11-20T10:00', 'completed': False}
    a = repo.StorePlanData({'coursework_id': item['id'], 'name': 'A'}, [task('Same'), task('Same')])
    b = repo.StorePlanData({'coursework_id': item['id'], 'name': 'B'}, [task('Same')])
    return path, repo, a, b


def app(path, mode='ok', backend=True):
    source = f'''
import streamlit as st
from folio.application import open_application
from folio_ui.follow_through import render_follow_through
from demos.src.coursework_service import RepositoryError
repo, _ = open_application({str(path)!r})
class FakeBackend:
    def set_completed(self, plan_id, task_id, completed, expected_completed):
        if {mode!r} == 'error': raise RepositoryError('private storage error')
        if {mode!r} == 'silent': return
        plan = repo.get_plan(plan_id)
        task = next(t for t in plan['tasks'] if t['id'] == task_id)
        if bool(task['completed']) != expected_completed: raise RepositoryError('stale')
        task['completed'] = completed
        repo.StorePlanData(plan['plan'], plan['tasks'])
    def get_reminder(self, task_id):
        return st.session_state.get('test_reminder_' + str(task_id), dict(enabled=False, remind_at=None, revision=0))
    def save_reminder(self, task_id, enabled, remind_at, expected_revision):
        if {mode!r} == 'error': raise RepositoryError('private storage error')
        if {mode!r} == 'silent': return
        st.session_state['test_reminder_' + str(task_id)] = dict(enabled=enabled, remind_at=remind_at, revision=expected_revision + 1)
render_follow_through(repo, {{t['id'] for t in repo.RestoreSavedApplicationState()['tasks']}}, FakeBackend() if {backend!r} else None)
'''
    return AppTest.from_string(source).run()


def button(a, label):
    return next(b for b in a.button if b.label == label)


@pytest.mark.parametrize('value', ['bad','2026-02-30T09:00','2026-11-20T9:00','2026-11-20T09:00Z','2026-11-20T09:00:00'])
def test_reminder_validation(value):
    with pytest.raises(ValueError): validate_reminder(True, value)
    assert validate_reminder(False, value) is None


def test_valid_local_time():
    assert validate_reminder(True, ' 2026-11-20T09:00 ') == '2026-11-20T09:00'


def test_default_controls_are_disabled_and_read_only(tmp_path):
    path, repo, _, _ = setup(tmp_path)
    before = repo.RestoreSavedApplicationState()
    a = app(path, backend=False)
    assert not a.exception
    assert all(b.disabled for b in a.button)
    assert all(c.disabled for c in a.checkbox)
    assert 'not connected' in a.info[0].value
    assert repo.RestoreSavedApplicationState() == before


def test_completion_undo_progress_and_plan_isolation(tmp_path):
    path, repo, first, second = setup(tmp_path)
    a = app(path)
    button(a, 'Mark complete').click().run()
    assert not a.exception
    assert repo.get_plan(first['plan']['id'])['tasks'][0]['completed'] == 1
    assert repo.get_plan(second['plan']['id']) == second
    assert any('1 of 2' in x.value for x in a.markdown)
    assert a.success[0].value == 'Congratulations! Task marked complete.'
    button(a, 'Mark incomplete').click().run()
    assert repo.get_plan(first['plan']['id'])['tasks'][0]['completed'] == 0
    assert 'Task marked incomplete.' in a.success[0].value


def test_congratulations_only_when_saved_plan_complete(tmp_path):
    path, repo, first, _ = setup(tmp_path)
    a = app(path)
    button(a, 'Mark complete').click().run()
    a.selectbox[0].select(first['tasks'][1]['id']).run()
    button(a, 'Mark complete').click().run()
    assert a.success[0].value == 'Congratulations! All tasks in this plan are complete.'
    a.run()
    assert not a.success
    restored = app(path)
    assert any('2 of 2' in x.value for x in restored.markdown)
    assert not restored.success


@pytest.mark.parametrize('mode', ['error', 'silent'])
def test_completion_failure_never_claims_success(tmp_path, mode):
    path, repo, _, _ = setup(tmp_path)
    before = repo.RestoreSavedApplicationState()
    a = app(path, mode)
    button(a, 'Mark complete').click().run()
    assert a.error and not a.success and not a.exception
    assert 'private' not in a.error[0].value
    assert repo.RestoreSavedApplicationState() == before


def test_reminder_enable_change_disable_validation(tmp_path):
    path, _, _, _ = setup(tmp_path)
    a = app(path)
    a.checkbox[0].check()
    a.text_input[0].set_value('bad')
    button(a, 'Save reminder').click().run()
    assert a.error and not a.success
    a.text_input[0].set_value('2026-11-20T08:45')
    button(a, 'Save reminder').click().run()
    assert not a.exception
    assert a.success[0].value == 'Reminder saved. Keep Folio and its browser session active.'
    assert a.checkbox[0].value
    a.text_input[0].set_value('2026-11-20T08:30')
    button(a, 'Save reminder').click().run()
    assert a.text_input[0].value == '2026-11-20T08:30'
    a.checkbox[0].uncheck()
    a.text_input[0].set_value('invalid ignored when disabling')
    button(a, 'Save reminder').click().run()
    assert 'Reminder disabled' in a.success[0].value
    assert not a.checkbox[0].value


def test_reminder_silent_failure_not_claimed_saved(tmp_path):
    path, _, _, _ = setup(tmp_path)
    a = app(path, 'silent')
    a.checkbox[0].check()
    button(a, 'Save reminder').click().run()
    assert a.error and not a.success


def test_empty_plan_and_empty_date(tmp_path):
    path, repo, a, b = setup(tmp_path)
    repo.StorePlanData(a['plan'], [])
    repo.StorePlanData(b['plan'], [])
    ui = app(path)
    assert not ui.exception and not ui.selectbox
    assert any('0 of 0' in x.value for x in ui.markdown)
