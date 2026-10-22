import io
import sqlite3

import pytest

from demos.src.coursework import validate_coursework
from demos.src.coursework_service import CourseworkService
from demos.src.csv_storage import SQLiteCourseworkRepository
from folio.application import open_application
from folio.storage import SCHEMA

BASE = dict(course='CS491', item_name='Assessment', due_date='2026-10-26')
START, END = '2026-10-24T23:00', '2026-10-25T01:00'


@pytest.mark.parametrize('changes,fields', [
    ({'start_time': START}, {'end_time'}),
    ({'end_time': END}, {'start_time'}),
    ({'start_time': '09:00', 'end_time': '10:00'}, {'start_time','end_time'}),
    ({'start_time': '2026-02-30T09:00', 'end_time': END}, {'start_time'}),
    ({'start_time': '2026-10-24T24:00', 'end_time': END}, {'start_time'}),
    ({'start_time': START, 'end_time': START}, {'end_time'}),
    ({'start_time': END, 'end_time': START}, {'end_time'}),
    ({'start_time': START + 'Z', 'end_time': END}, {'start_time'}),
])
def test_invalid_time_fields(changes, fields):
    result = validate_coursework({**BASE, **changes})
    assert {error['field'] for error in result['errors']} == fields


@pytest.mark.parametrize('adapter', ['academic','demo'])
def test_csv_manual_edit_and_restart(tmp_path, adapter):
    path = tmp_path / 'times.sqlite3'
    if adapter == 'academic':
        repository, service = open_application(path)
    else:
        repository = SQLiteCourseworkRepository(path)
        service = CourseworkService(repository)
    csv = io.StringIO(f'course,item_name,due_date,start_time,end_time\nCS491,Assessment,2026-10-26, {START} ,{END}\nCS491,Invalid,2026-10-26,09:00,10:00\n')
    result = service.import_coursework_csv(csv)
    assert result['accepted_count'] == result['rejected_count'] == 1
    saved = result['records'][0]
    assert saved['start_time'] == START and saved['end_time'] == END
    assert not service.edit_coursework(saved['id'], {'end_time': START})['success']
    with repository.transaction() as transaction:
        assert transaction.get(saved['id']) == saved
    # Partial edits preserve the untouched endpoint; blanking both removes the interval.
    assert service.edit_coursework(saved['id'], {'end_time': '2026-10-25T02:00'})['success']
    assert service.edit_coursework(saved['id'], {'start_time': '', 'end_time': ''})['success']
    manual = service.create_coursework({**BASE, 'item_name': 'Manual', 'start_time': START, 'end_time': END})
    assert manual['success']
    if adapter == 'academic':
        restarted, _ = open_application(path)
        assert restarted.restore_saved_application_state()['coursework'][-1] == manual['record']
    else:
        with SQLiteCourseworkRepository(path).transaction() as transaction:
            assert transaction.get(manual['record']['id']) == manual['record']


def test_v1_upgrade_preserves_records_and_relationships(tmp_path):
    path = tmp_path / 'v1.sqlite3'
    with sqlite3.connect(path) as connection:
        for statement in SCHEMA:
            connection.execute(statement)
        connection.execute("INSERT INTO coursework(id,course,item_name,due_date,source) VALUES(7,'C','A','2026-10-26','csv')")
        connection.execute("INSERT INTO plans(id,coursework_id,name) VALUES(11,7,'Plan')")
        connection.execute("INSERT INTO tasks(id,plan_id,name,start_time,end_time) VALUES(13,11,'Task',?,?)", (START, END))
        connection.execute("INSERT INTO feedback(id,plan_id,suggestion) VALUES(17,11,'Feedback')")
        connection.execute('PRAGMA user_version=1')
    repository, service = open_application(path)
    state = repository.restore_saved_application_state()
    assert state['coursework'][0]['start_time'] is None
    assert state['plans'][0]['coursework_id'] == 7
    assert state['tasks'][0]['id'] == 13 and state['feedback'][0]['id'] == 17
    assert service.edit_coursework(7, {'start_time': START, 'end_time': END})['success']
    repository.initialize()  # Repeat startup must not attempt the migration again.
    with sqlite3.connect(path) as connection:
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 2
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
    with repository.transaction() as transaction:
        assert transaction.get(7)['start_time'] == START


def test_upgrade_failure_is_atomic(tmp_path):
    path = tmp_path / 'bad-v1.sqlite3'
    with sqlite3.connect(path) as connection:
        # Simulate a partially modified v1 schema: second ALTER must fail.
        connection.execute('CREATE TABLE coursework(id INTEGER PRIMARY KEY, end_time TEXT)')
        connection.execute('INSERT INTO coursework VALUES(1,NULL)')
        connection.execute('PRAGMA user_version=1')
    from demos.src.coursework_service import RepositoryError
    with pytest.raises(RepositoryError):
        open_application(path)
    with sqlite3.connect(path) as connection:
        assert [row[1] for row in connection.execute('PRAGMA table_info(coursework)')] == ['id','end_time']
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 1
