from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from folio.application import open_application
from folio.scheduling import ScheduleService


def task(start, end, name='Review'):
    return {'name': name, 'start_time': start, 'end_time': end}


def fixture(tmp_path):
    path = tmp_path / 'schedule.sqlite3'
    repo, coursework = open_application(path)
    first = coursework.create_coursework({'course': 'CS', 'item_name': 'Essay', 'due_date': '2026-10-26'})['record']
    second = coursework.create_coursework({'course': 'MATH', 'item_name': 'Exam', 'due_date': '2026-10-26'})['record']
    a = repo.StorePlanData({'coursework_id': first['id'], 'name': 'Plan A'}, [
        task('2026-10-19T10:00', '2026-10-19T11:00'),
        task('2026-10-20T10:00', '2026-10-20T11:00')])
    b = repo.StorePlanData({'coursework_id': second['id'], 'name': 'Plan B'}, [
        task('2026-10-19T11:00', '2026-10-19T12:00')])
    return path, repo, a, b


@pytest.mark.parametrize('start,end,conflict', [
    ('09:00', '10:00', False), ('09:30', '10:30', True), ('09:30', '11:30', True),
    ('10:00', '11:00', True), ('10:15', '10:45', True), ('10:30', '11:30', True),
    ('11:00', '12:00', False),
])
@pytest.mark.parametrize('same_plan', [False, True])
def test_c8_every_interval_and_both_indicators(tmp_path, start, end, conflict, same_plan):
    _, repo, a, b = fixture(tmp_path)
    repo.StorePlanData(b['plan'], [])
    target = a if same_plan else b
    items = a['tasks'] if same_plan else []
    saved = repo.StorePlanData(target['plan'], [*items, task(f'2026-10-19T{start}', f'2026-10-19T{end}')])
    candidate = saved['tasks'][-1]['id']
    rows = {t['id']: t for t in ScheduleService(repo).tasks()}
    first = a['tasks'][0]['id']
    assert (candidate in rows[first]['conflict_ids']) is conflict
    assert (first in rows[candidate]['conflict_ids']) is conflict
    assert len(rows) == 3


def test_daily_weekly_identity_edits_removal_and_restart(tmp_path):
    path, repo, a, b = fixture(tmp_path)
    service = ScheduleService(repo)
    assert len(service.tasks(date(2026, 10, 19))) == 2
    assert len(service.tasks(date(2026, 10, 21), weekly=True)) == 3
    assert len({t['id'] for t in service.tasks()}) == 3
    assert {t['course'] for t in service.tasks()} == {'CS', 'MATH'}
    assert all(not t['conflict_ids'] for t in service.tasks())
    first_id = a['tasks'][0]['id']
    service.correct_time(first_id, '2026-10-19T09:00', '2026-10-19T10:00')
    before = repo.get_plan(a['plan']['id'])
    with pytest.raises(ValueError, match='Saved time unchanged'):
        service.correct_time(first_id, '2026-10-19T11:30', '2026-10-19T12:30')
    assert repo.get_plan(a['plan']['id']) == before
    repo.StorePlanData(before['plan'], before['tasks'][:1])
    reopened, _ = open_application(path)
    rows = ScheduleService(reopened).tasks()
    assert len(rows) == 2
    assert rows[0]['id'] == first_id and rows[0]['plan_id'] == a['plan']['id']
    assert rows[0]['start_time'] == '2026-10-19T09:00'
    assert reopened.get_plan(b['plan']['id']) == b
    repo.StorePlanData({**b['plan'], 'active': False})
    assert len(service.tasks()) == 1


def test_multiple_conflicts_and_resolution(tmp_path):
    _, repo, a, b = fixture(tmp_path)
    saved = repo.StorePlanData(a['plan'], [*a['tasks'], task('2026-10-19T10:30', '2026-10-19T11:30')])
    rows = ScheduleService(repo).tasks()
    added_id = saved['tasks'][-1]['id']
    assert len(next(t for t in rows if t['id'] == added_id)['conflict_ids']) == 2
    assert sum(bool(t['conflict_ids']) for t in rows) == 3
    ScheduleService(repo).correct_time(added_id, '2026-10-19T12:00', '2026-10-19T13:00')
    assert not any(t['conflict_ids'] for t in ScheduleService(repo).tasks())


def test_other_date_and_overnight_window_boundaries(tmp_path):
    _, repo, a, b = fixture(tmp_path)
    repo.StorePlanData(a['plan'], [task('2026-10-18T23:00', '2026-10-19T01:00')])
    repo.StorePlanData(b['plan'], [task('2026-10-18T23:30', '2026-10-18T23:45'),
                                 task('2026-10-20T23:00', '2026-10-21T01:00')])
    service = ScheduleService(repo)
    assert len(service.tasks(date(2026, 10, 19))) == 1
    assert len(service.tasks(date(2026, 10, 21))) == 1
    source = f"from folio.application import open_application\nfrom folio_ui.scheduling import render_schedule\nrender_schedule(open_application({str(repo.database_path)!r})[0])"
    app = AppTest.from_string(source).run()
    app.date_input[0].set_value(date(2026, 10, 19)).run()
    assert not app.exception
    assert '23:30' in app.warning[0].value


@pytest.mark.parametrize('start,end', [('bad', 'bad'), ('2026-10-19T12:00','2026-10-19T11:00'),
                                      ('2026-10-19T10:00Z','2026-10-19T11:00Z')])
def test_invalid_correction_preserves_data(tmp_path, start, end):
    _, repo, a, _ = fixture(tmp_path)
    before = repo.RestoreSavedApplicationState()
    with pytest.raises(ValueError):
        ScheduleService(repo).correct_time(a['tasks'][0]['id'], start, end)
    assert repo.RestoreSavedApplicationState() == before


def test_plan_editor_rejects_nonlocal_times_before_schedule(tmp_path):
    from folio.planning import PlanningService
    _, repo, a, _ = fixture(tmp_path)
    before = repo.RestoreSavedApplicationState()
    a['tasks'][0]['start_time'] += 'Z'
    with pytest.raises(ValueError, match='valid start and end'):
        PlanningService(repo).save_plan(a)
    assert repo.RestoreSavedApplicationState() == before


def test_save_notices_identify_every_pair_once_and_only_affected_plan(tmp_path):
    from folio.scheduling import plan_conflict_messages
    _, repo, a, b = fixture(tmp_path)
    repo.StorePlanData(a['plan'], [*a['tasks'], task('2026-10-19T10:30', '2026-10-19T11:30')])
    tasks = ScheduleService(repo).tasks()
    assert len(plan_conflict_messages(tasks, a['plan']['id'])) == 2
    assert len(plan_conflict_messages(tasks, b['plan']['id'])) == 1
    assert plan_conflict_messages(tasks, 999) == []
