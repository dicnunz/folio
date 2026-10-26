from datetime import date, datetime
import sqlite3

import pytest

from demos.src.scheduling import Schedule, Task, combine_active_tasks, schedule_window
from demos.src.coursework_service import RepositoryError
from folio.application import open_application
from folio.schedule_service import ScheduleService
from scripts.seed_schedule_fixture import seed

DAY = '2026-10-26'


def domain_state(start='09:30', end='10:30', same_plan=False, other_day=DAY):
    return {'coursework': [{'id': 1, 'course': 'Math'}, {'id': 2, 'course': 'CS'}],
            'plans': [{'id': 10, 'name': 'A', 'active': 1, 'coursework_id': 1},
                      {'id': 20, 'name': 'B', 'active': 1, 'coursework_id': 2}],
            'tasks': [{'id': 101, 'plan_id': 10, 'name': 'Review', 'start_time': DAY+'T10:00', 'end_time': DAY+'T11:00'},
                      {'id': 202, 'plan_id': 10 if same_plan else 20, 'name': 'Review',
                       'start_time': other_day+'T'+start, 'end_time': other_day+'T'+end}]}


@pytest.mark.parametrize('same_plan', [False, True])
@pytest.mark.parametrize('start,end,conflict', [
    ('09:00','10:00',False), ('09:30','10:30',True), ('09:30','11:30',True),
    ('10:00','11:00',True), ('10:15','10:45',True), ('10:30','11:30',True), ('11:00','12:00',False)])
def test_c8_every_interval_within_and_across_plans(start, end, conflict, same_plan):
    result = combine_active_tasks(domain_state(start, end, same_plan))
    assert not result['errors']
    rows = {row['id']: row for row in result['tasks']}
    assert rows[101]['conflict_ids'] == ([202] if conflict else [])
    assert rows[202]['conflict_ids'] == ([101] if conflict else [])
    assert rows[101]['name'] == rows[202]['name']
    assert rows[202]['plan_id'] == (10 if same_plan else 20)
    assert rows[202]['course'] == ('Math' if same_plan else 'CS')


def test_c8_different_dates_and_inactive_plans_do_not_conflict():
    state = domain_state('10:00','11:00', other_day='2026-10-27')
    assert all(not row['conflict_ids'] for row in combine_active_tasks(state)['tasks'])
    state['plans'][1]['active'] = 0
    assert [row['id'] for row in combine_active_tasks(state)['tasks']] == [101]


def test_overnight_window_boundaries_and_week_rollover():
    state = domain_state('00:00','01:00', other_day='2026-10-27')
    state['tasks'][0].update(start_time='2026-10-26T23:00', end_time='2026-10-27T00:30')
    tasks = combine_active_tasks(state)['tasks']
    assert tasks[0]['conflict_ids'] == [202]
    assert len(schedule_window(tasks, date(2026,10,26),'Daily')) == 1
    assert len(schedule_window(tasks, date(2026,10,27),'Daily')) == 2
    assert schedule_window(tasks, date(2026,10,25),'Weekly') == []
    assert len(schedule_window(tasks, date(2026,11,1),'Weekly')) == 2
    # Ending exactly at midnight is excluded from the following day.
    state['tasks'][0]['end_time'] = '2026-10-27T00:00'
    tasks = combine_active_tasks(state)['tasks']
    assert len(schedule_window(tasks, date(2026,10,27),'Daily')) == 1


def test_existing_schedule_accepts_dated_tasks_and_keeps_numeric_api():
    schedule = Schedule()
    first = Task(1,1,'Read',datetime(2026,10,26,10),datetime(2026,10,26,11))
    second = Task(2,2,'Read',datetime(2026,10,26,10,30),datetime(2026,10,26,11,30))
    schedule.add_task(first)
    assert schedule.add_task(second) == [first]
    assert schedule.reschedule_task(2,datetime(2026,10,26,11),datetime(2026,10,26,12)) == []


@pytest.fixture
def saved(tmp_path):
    path = tmp_path / 'schedule.sqlite3'
    seed(path)
    repository, _ = open_application(path)
    return repository, ScheduleService(repository)


def test_c9_every_conflict_then_student_resolution(saved):
    repository, service = saved
    rows = {row['id']: row for row in service.get_schedule()['tasks']}
    assert rows[1]['conflict_ids'] == [2]
    assert rows[2]['conflict_ids'] == [1,4]
    assert rows[4]['conflict_ids'] == [2]
    before = repository.restore_saved_application_state()
    rejected = service.reschedule_task(2, DAY+'T10:15', DAY+'T11:45')
    assert not rejected['success']
    assert {row['id'] for row in rejected['conflicts']} == {1,4}
    assert repository.restore_saved_application_state() == before
    result = service.reschedule_task(2, DAY+'T12:00', DAY+'T13:00')
    assert result['success'] and result['record']['plan_id'] == 1
    assert all(not row['conflict_ids'] for row in service.get_schedule()['tasks'])
    after = repository.restore_saved_application_state()
    assert after['tasks'][0] == before['tasks'][0]
    assert after['tasks'][3] == before['tasks'][3]


def test_c7_plan_edits_task_deletion_and_restart_preserve_associations(saved):
    repository, service = saved
    other = repository.get_plan(2)
    assert service.reschedule_task(1,'2026-10-28T09:00','2026-10-28T10:00')['success']
    a = repository.get_plan(1)
    a['plan']['name'] = 'Edited plan'
    a['tasks'] = [row for row in a['tasks'] if row['id'] != 2]
    repository.StorePlanData(**a)
    reopened, _ = open_application(repository.database_path)
    rows = {row['id']: row for row in ScheduleService(reopened).get_schedule()['tasks']}
    assert set(rows) == {1,3,4}
    assert rows[1]['plan'] == 'Edited plan' and rows[1]['plan_id'] == 1
    assert rows[1]['start_time'] == '2026-10-28T09:00'
    assert reopened.get_plan(2) == other


def test_plan_deactivation_reactivation_and_deletion_refresh_schedule(saved):
    repository, service = saved
    original_coursework = repository.restore_saved_application_state()['coursework']
    plan = repository.get_plan(1)['plan']
    repository.StorePlanData({**plan, 'active': False})
    assert [row['id'] for row in service.get_schedule()['tasks']] == [4]
    assert not service.reschedule_task(1, DAY+'T08:00',DAY+'T09:00')['success']
    repository.StorePlanData(plan)
    assert len(service.get_schedule()['tasks']) == 4
    repository.delete_plan(1)
    assert [row['id'] for row in service.get_schedule()['tasks']] == [4]
    assert repository.restore_saved_application_state()['coursework'] == original_coursework
    assert repository.restore_saved_application_state()['feedback'] == []
    with pytest.raises(RepositoryError): repository.delete_plan(999)


def test_n3_daily_weekly_and_rejected_correction(saved):
    repository, service = saved
    a = repository.get_plan(1)
    a['tasks'] = [task for task in a['tasks'] if task['id'] != 2]
    repository.StorePlanData(**a)
    assert {row['id'] for row in schedule_window(service.get_schedule()['tasks'],date(2026,10,26),'Daily')} == {1,4}
    assert {row['id'] for row in schedule_window(service.get_schedule()['tasks'],date(2026,10,26),'Weekly')} == {1,3,4}
    assert service.reschedule_task(1, DAY+'T09:00',DAY+'T10:00')['success']
    rejected = service.reschedule_task(1,DAY+'T11:30',DAY+'T12:30')
    assert not rejected['success'] and [row['id'] for row in rejected['conflicts']] == [4]
    assert repository.get_plan(1)['tasks'][0]['start_time'] == DAY+'T09:00'


@pytest.mark.parametrize('start,end', [('bad','bad'),(DAY+'T24:00',DAY+'T25:00'),(DAY+'T12:00',DAY+'T12:00'),(DAY+'T13:00',DAY+'T12:00')])
def test_invalid_times_preserve_saved_records(saved,start,end):
    repository, service = saved
    before = repository.restore_saved_application_state()
    result = service.reschedule_task(1,start,end)
    assert not result['success'] and result['errors']
    assert repository.restore_saved_application_state() == before


def test_missing_and_stale_task_preserve_data(saved):
    repository, service = saved
    assert not service.reschedule_task(999,DAY+'T08:00',DAY+'T09:00')['success']
    assert service.reschedule_task(1,DAY+'T08:00',DAY+'T09:00')['success']
    before = repository.restore_saved_application_state()
    rejected = service.reschedule_task(1,DAY+'T07:00',DAY+'T08:00',expected_times=(DAY+'T10:00',DAY+'T11:00'))
    assert not rejected['success'] and 'changed' in rejected['errors'][0]['message']
    assert repository.restore_saved_application_state() == before


def test_invalid_saved_times_are_reported_and_block_unsafe_correction(saved):
    repository, service = saved
    with sqlite3.connect(repository.database_path) as connection:
        connection.execute("UPDATE tasks SET start_time='2026-02-30T09:00',end_time='2026-02-30T10:00' WHERE id=1")
    schedule = service.get_schedule()
    assert schedule['errors'][0]['task_id'] == 1
    assert not service.reschedule_task(2,DAY+'T12:00',DAY+'T13:00')['success']


@pytest.mark.parametrize('operation', ['reschedule','delete_plan','commit'])
def test_failed_writes_roll_back(saved,operation):
    repository, service = saved
    before = repository.restore_saved_application_state()
    with sqlite3.connect(repository.database_path) as connection:
        if operation == 'reschedule':
            connection.execute("CREATE TRIGGER fail BEFORE UPDATE ON tasks BEGIN SELECT RAISE(ABORT,'test failure'); END")
        elif operation == 'delete_plan':
            connection.execute("CREATE TRIGGER fail BEFORE DELETE ON plans BEGIN SELECT RAISE(ABORT,'test failure'); END")
        else:
            connection.executescript('''CREATE TABLE parent (id INTEGER PRIMARY KEY);
                CREATE TABLE audit (id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED);
                CREATE TRIGGER fail AFTER UPDATE ON tasks BEGIN INSERT INTO audit VALUES(999); END;''')
    if operation == 'delete_plan':
        with pytest.raises(RepositoryError): repository.delete_plan(1)
    else:
        result = service.reschedule_task(2,DAY+'T12:00',DAY+'T13:00')
        assert not result['success'] and result['errors'][0]['field'] == 'storage'
    assert repository.restore_saved_application_state() == before
