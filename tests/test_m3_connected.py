from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from demos.src.coursework_service import RepositoryError
from folio.application import open_application
from folio.follow_through import FollowThrough
from folio.planning import PlanningService
from folio.schedule_service import ScheduleService as TransactionalSchedule
from folio.scheduling import ScheduleService


def make_plan(path):
    repository, coursework = open_application(path)
    quiz = coursework.create_coursework({
        'course': 'Synthetic', 'item_name': 'Quiz', 'due_date': '2026-11-20',
        'start_time': '2026-11-20T10:00', 'end_time': '2026-11-20T11:00',
    })['record']
    repository.set_preparation_cutoff(quiz['id'], '2026-11-20T10:00')
    plan = {'coursework_id': quiz['id'], 'name': 'Quiz plan'}
    task = {
        'name': 'Study', 'preparation': True,
        'start_time': '2026-11-20T08:30', 'end_time': '2026-11-20T09:00',
    }
    first = repository.store_plan_data(plan, [task])
    second = repository.store_plan_data({**plan, 'name': 'Other plan'}, [
        {**task, 'start_time': '2026-11-20T08:00', 'end_time': '2026-11-20T08:30'},
    ])
    return repository, first, second


def test_completion_idempotent_isolated_and_not_overwritten_by_plan_save(tmp_path):
    path = tmp_path / 'academic.sqlite3'
    repository, first, second = make_plan(path)
    plan_id, task_id = first['plan']['id'], first['tasks'][0]['id']
    backend = FollowThrough(repository)
    planning = PlanningService(repository)
    old_draft = planning.open_plan(plan_id)
    backend.set_completed(plan_id, task_id, True, False)
    backend.set_completed(plan_id, task_id, True, False)
    old_draft['plan']['notes'] = 'Other edit'
    assert planning.save_plan(old_draft)['tasks'][0]['completed']
    with pytest.raises(RepositoryError):
        backend.set_completed(second['plan']['id'], task_id, False, True)
    reopened, _ = open_application(path)
    assert reopened.get_plan(plan_id)['tasks'][0]['completed']
    assert reopened.get_plan(second['plan']['id']) == second
    FollowThrough(reopened).set_completed(plan_id, task_id, False, True)
    assert not reopened.get_plan(plan_id)['tasks'][0]['completed']


def test_reminder_revisions_disable_reopen_and_once_delivery(tmp_path):
    path = tmp_path / 'academic.sqlite3'
    repository, first, second = make_plan(path)
    a, b = first['tasks'][0]['id'], second['tasks'][0]['id']
    backend = FollowThrough(repository)
    backend.save_reminder(a, True, '2026-11-20T08:30', 0)
    backend.save_reminder(b, True, '2026-11-20T08:30', 0)
    backend.save_reminder(b, False, None, 1)
    with pytest.raises(ValueError, match='Reminder changed'):
        backend.save_reminder(a, False, None, 0)
    assert backend.claim_due(datetime(2026, 11, 20, 8, 29)) == []
    reopened, _ = open_application(path)
    backend = FollowThrough(reopened)
    assert backend.get_reminder(a)['remind_at'] == '2026-11-20T08:30'
    assert [row['task_id'] for row in backend.claim_due(datetime(2026, 11, 20, 8, 30))] == [a]
    assert backend.claim_due(datetime(2026, 11, 20, 8, 31)) == []
    backend.save_reminder(a, True, '2026-11-20T08:32', 1)
    assert [row['task_id'] for row in backend.claim_due(datetime(2026, 11, 20, 8, 32))] == [a]


def test_deadline_blocks_plan_and_both_schedule_paths_without_mutation(tmp_path):
    repository, first, _ = make_plan(tmp_path / 'academic.sqlite3')
    task_id = first['tasks'][0]['id']
    snapshot = repository.restore_saved_application_state()
    planning, schedule = PlanningService(repository), ScheduleService(repository)
    draft = planning.open_plan(first['plan']['id'])
    draft['tasks'][0]['end_time'] = '2026-11-20T10:01'
    for action in (
        lambda: planning.save_plan(draft),
        lambda: schedule.correct_time(task_id, '2026-11-20T08:30', '2026-11-20T10:01'),
    ):
        with pytest.raises(ValueError, match='Study.*Quiz.*10:00'):
            action()
        assert repository.restore_saved_application_state() == snapshot
    response = TransactionalSchedule(repository).reschedule_task(
        task_id, '2026-11-20T08:30', '2026-11-20T10:01')
    assert not response['success']
    assert repository.restore_saved_application_state() == snapshot
    schedule.correct_time(task_id, '2026-11-20T08:30', '2026-11-20T10:00')
    assert repository.get_plan(first['plan']['id'])['tasks'][0]['end_time'].endswith('10:00')


def test_real_screen_saves_progress_reopens_and_undoes(tmp_path, monkeypatch):
    path = tmp_path / 'academic.sqlite3'
    repository, first, second = make_plan(path)
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    app_file = Path(__file__).resolve().parents[1] / 'app.py'
    plan_id, task_id = first['plan']['id'], first['tasks'][0]['id']

    def schedule_app():
        app = AppTest.from_file(str(app_file)).run()
        app.radio(key='folio_screen').set_value('Schedule').run()
        app.date_input(key='schedule_date').set_value(datetime(2026, 11, 20).date()).run()
        app.selectbox(key='follow_through_task').select(task_id).run()
        assert not app.exception
        return app

    app = schedule_app()
    next(button for button in app.button if button.label == 'Mark complete').click().run()
    assert repository.get_plan(plan_id)['tasks'][0]['completed']
    assert repository.get_plan(second['plan']['id']) == second
    assert any('All tasks in this plan are complete' in message.value for message in app.success)
    app = schedule_app()
    next(button for button in app.button if button.label == 'Mark incomplete').click().run()
    assert not repository.get_plan(plan_id)['tasks'][0]['completed']


def test_deadline_meaning_changed_coursework_and_independent_correction(tmp_path):
    path = tmp_path / 'academic.sqlite3'
    repository, first, second = make_plan(path)
    cid = first['plan']['coursework_id']
    repository.set_preparation_cutoff(cid, '')
    repository.store_coursework('UPDATE', {**repository.restore_saved_application_state()['coursework'][0],
                                'start_time': '2026-11-20T06:00', 'end_time': '2026-11-20T07:00'})
    schedule = ScheduleService(repository)
    assert all(row['preparation_notice'][0] == 'unknown' for row in schedule.tasks())
    tid = first['tasks'][0]['id']
    schedule.correct_time(tid, '2026-11-20T16:00', '2026-11-20T17:00')
    with pytest.raises(ValueError, match='on or before 2026-11-20'):
        schedule.correct_time(tid, '2026-11-20T23:55', '2026-11-21T00:01')
    repository.set_preparation_cutoff(cid, '2026-11-20T08:00')
    assert len([row for row in schedule.tasks() if row['preparation_notice'][0] == 'late']) == 2
    assert not repository.get_plan(first['plan']['id'])['tasks'][0]['completed']
    schedule.correct_time(tid, '2026-11-20T07:00', '2026-11-20T08:00')
    assert repository.get_plan(second['plan']['id']) == second
    assert sum('preparation_notice' in row for row in schedule.tasks()) == 1
    other = repository.get_plan(second['plan']['id'])
    del other['tasks'][0]['preparation']
    other['tasks'][0]['name'] = 'Previously saved study'
    assert repository.store_plan_data(**other)['tasks'][0]['preparation']
    with pytest.raises(ValueError):
        repository.set_preparation_cutoff(cid, '2026-11-20T25:00')
    assert repository.preparation_contexts()[cid]['cutoff'] == '2026-11-20T08:00'
    with pytest.raises(RepositoryError):
        repository.set_preparation_cutoff(9999, '2026-11-20T12:00')


def test_plan_can_fix_one_of_two_late_tasks_without_rewriting_other_or_completed_history(tmp_path):
    repository, first, _ = make_plan(tmp_path / 'academic.sqlite3')
    plan = first['plan']
    original = first['tasks'][0]
    saved = repository.store_plan_data(plan, [original, {**{k:v for k,v in original.items() if k != 'id'},
                  'start_time': '2026-11-20T09:00', 'end_time': '2026-11-20T09:25', 'completed': True}])
    repository.set_preparation_cutoff(plan['coursework_id'], '2026-11-20T08:15')
    draft = PlanningService(repository).open_plan(plan['id'])
    draft['tasks'][0].update(start_time='2026-11-19T23:50', end_time='2026-11-20T00:05')
    assert PlanningService(repository).save_plan(draft)['tasks'][1] == saved['tasks'][1]
    draft = PlanningService(repository).open_plan(plan['id'])
    draft['tasks'][0].update(start_time='2026-11-20T12:00', end_time='2026-11-20T12:30', preparation=False)
    assert not PlanningService(repository).save_plan(draft)['tasks'][0]['preparation']
    status = TransactionalSchedule(repository).reschedule_task(saved['tasks'][1]['id'], '2026-11-20T11:55', '2026-11-20T12:15')
    assert {error['field'] for error in status['errors']} == {'end_time','times'}


def test_reminders_review_cancel_and_overdue(tmp_path):
    path = tmp_path / 'academic.sqlite3'
    repository, first, second = make_plan(path)
    plan_id, a, b = first['plan']['id'], first['tasks'][0]['id'], second['tasks'][0]['id']
    backend = FollowThrough(repository)
    when = '2026-11-20T08:20'
    due = datetime(2026,11,20,8,25)
    backend.save_reminder(a, True, when, 0)
    backend.save_reminder(b, True, when, 0)
    ScheduleService(repository).correct_time(a, '2026-11-20T09:00', '2026-11-20T09:30')
    setting = backend.get_reminder(a)
    assert setting['needs_review'] and not setting['enabled'] and setting['remind_at'] == when
    repository.delete_plan(second['plan']['id'])
    assert backend.claim_due(due) == []
    with pytest.raises(ValueError, match='Reminder changed'):
        backend.save_reminder(a, True, when, 1)
    backend.save_reminder(a, True, when, setting['revision'])
    assert backend.set_completed(plan_id, a, True, False)
    assert backend.set_completed(plan_id, a, True, False) is False
    assert not backend.get_reminder(a)['enabled']
    assert backend.claim_due(due) == []
    with pytest.raises(ValueError, match='incomplete'):
        backend.save_reminder(a, True, when, backend.get_reminder(a)['revision'])
    backend.set_completed(plan_id, a, False, True)
    assert backend.claim_due(due) == []
    backend.save_reminder(a, True, when, backend.get_reminder(a)['revision'])
    reopened = FollowThrough(open_application(path)[0])
    alerts = reopened.claim_due(due)
    assert len(alerts) == 1 and alerts[0]['overdue'] and alerts[0]['task_id'] == a
    assert reopened.claim_due(due) == []


def test_real_screens_cutoff_and_selected_exports(tmp_path, monkeypatch):
    from email import policy
    from email.parser import BytesParser
    from io import BytesIO
    import subprocess
    from zipfile import ZipFile

    path = tmp_path / 'private.sqlite3'
    repository, first, second = make_plan(path)
    cid, tid = first['plan']['coursework_id'], first['tasks'][0]['id']
    backend = FollowThrough(repository)
    private_time = '2041-03-17T17:34'
    backend.save_reminder(tid, True, private_time, 0)
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()

    def click(label):
        next(b for b in app.button if b.label == label).click().run()
        assert not app.exception

    app.selectbox(key='coursework_picker').set_value(cid).run()
    exact = next(t for t in app.text_input if t.label.startswith('Assessment start or submission cutoff'))
    exact.set_value('2026-11-20T08:59')
    click('Save cutoff')
    app.radio(key='folio_screen').set_value('Schedule').run()
    app.date_input(key='schedule_date').set_value(datetime(2026,11,20).date()).run()
    assert any('Finish by 2026-11-20 08:59' in w.value for w in app.warning)
    app.radio(key='folio_screen').set_value('Plan').run()
    app.selectbox[1].set_value(first['plan']['id']).run()
    click('Open saved plan')
    assert any('Finish by 2026-11-20 08:59' in w.value for w in app.warning)
    app.radio(key='folio_screen').set_value('Share').run()
    app.multiselect(key='share_fields').set_value(['name', 'tasks']).run()
    click('Prepare PDF and DOCX')
    click('Prepare instructor email')
    click('Create unsent email file')
    eml = BytesParser(policy=policy.default).parsebytes(app.session_state['share_email'])
    assert not eml['To']
    private = (private_time, '08:59', 'Other plan', 'reminder', 'completed', 'preparation')
    def check(text):
        assert 'Study' in text
        assert all(value.lower() not in text.lower() for value in private)

    check(app.text[0].value)
    check(eml.get_body(preferencelist=('plain',)).get_content())
    parts = {p.get_filename():p.get_payload(decode=True) for p in eml.iter_attachments()}
    assert set(parts) == {'academic-plan.pdf', 'academic-plan.docx'}
    for data in (app.session_state['share_pdf'], parts['academic-plan.pdf']):
        check(subprocess.run(['pdftotext','-','-'],input=data, capture_output=True, check=True).stdout.decode())
    for data in (app.session_state['share_docx'], parts['academic-plan.docx']):
        with ZipFile(BytesIO(data)) as doc:
            check(doc.read('word/document.xml').decode())
    assert backend.get_reminder(tid)['remind_at'] == private_time
    assert repository.get_plan(second['plan']['id']) == second
