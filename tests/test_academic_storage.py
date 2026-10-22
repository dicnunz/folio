import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from time import perf_counter

import pytest

from demos.src.coursework_service import RepositoryError
from folio.application import open_application
from folio.storage import AcademicRepository
from scripts.seed_academic_fixture import seed


@pytest.fixture
def application(tmp_path):
    return open_application(tmp_path / "academic.sqlite3")


def create(service, name="Assignment"):
    result = service.create_coursework({"course": "CS491", "item_name": name, "due_date": "2026-10-26"})
    assert result["success"]
    return result["record"]


def task(name="Read"):
    return {"name": name, "start_time": "2026-10-22T10:00", "end_time": "2026-10-22T11:00", "completed": False}


def test_fresh_database_restart_and_version(application):
    repository, _ = application
    empty = {"coursework": [], "plans": [], "tasks": [], "feedback": []}
    assert repository.RestoreSavedApplicationState() == empty
    repository.initialize()
    assert repository.RestoreSavedApplicationState() == empty
    with sqlite3.connect(repository.database_path) as connection:
        assert connection.execute('PRAGMA user_version').fetchone()[0] == 2
        assert connection.execute('PRAGMA foreign_key_check').fetchall() == []


def test_c6_latest_academic_state_across_process_restart(tmp_path):
    path = tmp_path / "fixture.sqlite3"
    seed(path)
    repository, service = open_application(path)
    first = repository.restore_saved_application_state()
    course = first["coursework"][0]
    assert service.edit_coursework(course["id"], {"item_name": "Latest assignment"})["success"]
    aggregate = repository.get_plan(first["plans"][0]["id"])
    aggregate["plan"]["name"] = "Latest plan"
    aggregate["tasks"][0]["name"] = "Latest task"
    aggregate["tasks"][0]["completed"] = True
    aggregate["feedback"][0]["adapted_text"] = "Latest entered feedback"
    saved = repository.StorePlanData(**aggregate)
    assert saved["tasks"][0]["id"] == first["tasks"][0]["id"]
    expected = repository.restore_saved_application_state()
    code = 'import json,sys; from folio.application import open_application; print(json.dumps(open_application(sys.argv[1])[0].RestoreSavedApplicationState()))'
    for _ in range(2):
        restored = json.loads(subprocess.check_output([sys.executable, '-c', code, str(path)], text=True))
        assert restored == expected
    assert len(restored["coursework"]) == 1 and len(restored["plans"]) == 2
    assert len(restored["tasks"]) == 4 and len(restored["feedback"]) == 2


def test_c7_identity_reschedule_delete_and_other_plan_preserved(tmp_path):
    path = tmp_path / "fixture.sqlite3"
    seed(path)
    repository, _ = open_application(path)
    a, b = repository.restore_saved_application_state()["plans"]
    plan_a, plan_b = repository.get_plan(a["id"]), repository.get_plan(b["id"])
    assert plan_a["tasks"][0]["name"] == plan_b["tasks"][0]["name"]
    assert plan_a["tasks"][0]["id"] != plan_b["tasks"][0]["id"]
    retained = plan_a["tasks"][0]
    retained.update(start_time="2026-10-24T12:00", end_time="2026-10-24T13:00")
    repository.StorePlanData(a, [retained], None)
    restored, _ = open_application(path)
    assert restored.get_plan(a["id"])["tasks"] == [retained]
    assert restored.get_plan(b["id"]) == plan_b
    assert restored.get_plan(a["id"])["feedback"] == plan_a["feedback"]


def test_store_coursework_contract_and_service_integration(application):
    repository, service = application
    record = create(service)
    record["item_name"] = "Updated"
    updated = repository.StoreCoursework("UPDATE", record)
    assert updated["id"] == record["id"] and updated["source"] == "manual"
    assert not service.create_coursework({})["success"]
    assert not service.create_coursework({key: updated[key] for key in ('course','item_name','due_date')})["success"]
    repository.StoreCoursework("DELETE", updated)
    assert repository.restore_saved_application_state()["coursework"] == []
    next_record = create(service, "Later")
    assert next_record["id"] > record["id"]


def test_real_relationship_checker_blocks_coursework_delete(application):
    repository, service = application
    course = create(service)
    repository.StorePlanData({"coursework_id": course["id"], "name": "Plan"}, [task()], [])
    before = repository.restore_saved_application_state()
    result = service.delete_coursework(course["id"])
    assert not result["success"] and result["errors"][0]["code"] == "dependent_records"
    with pytest.raises(RepositoryError):
        repository.StoreCoursework("DELETE", course)
    assert repository.restore_saved_application_state() == before


def test_child_cannot_be_moved_and_plan_cannot_be_reassigned(application):
    repository, service = application
    first, second = create(service), create(service, "Other")
    a = repository.StorePlanData({"coursework_id": first["id"], "name": "A"}, [task()], [])
    b = repository.StorePlanData({"coursework_id": second["id"], "name": "B"}, [task()], [])
    before = repository.restore_saved_application_state()
    with pytest.raises(RepositoryError):
        repository.StorePlanData({**a["plan"], "name": "Must roll back"}, b["tasks"], [])
    with pytest.raises(RepositoryError):
        repository.StorePlanData({**a["plan"], "coursework_id": second["id"]}, None, None)
    assert repository.restore_saved_application_state() == before


@pytest.mark.parametrize("bad_part", ['task', 'feedback', 'duplicate_id', 'missing_coursework'])
def test_aggregate_failure_rolls_back_every_table(application, bad_part):
    repository, service = application
    course = create(service)
    saved = repository.StorePlanData({"coursework_id": course["id"], "name": "Original"}, [task()], [{"suggestion": "Original feedback"}])
    before = repository.restore_saved_application_state()
    plan, tasks, feedback = saved['plan'], saved['tasks'], saved['feedback']
    plan['name'] = 'Should not be saved'
    if bad_part == 'task': tasks.append({**task(), 'end_time': '2020-01-01T00:00'})
    if bad_part == 'feedback': feedback.append({'suggestion': 'bad', 'decision': 'invalid'})
    if bad_part == 'duplicate_id': tasks.append(tasks[0].copy())
    if bad_part == 'missing_coursework': plan['coursework_id'] = 999
    with pytest.raises(RepositoryError):
        repository.StorePlanData(plan, tasks, feedback)
    assert repository.restore_saved_application_state() == before


def test_commit_failure_rolls_back_aggregate(application):
    repository, service = application
    course = create(service)
    with sqlite3.connect(repository.database_path) as connection:
        connection.executescript('''CREATE TABLE parent (id INTEGER PRIMARY KEY);
        CREATE TABLE audit (parent_id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED);
        CREATE TRIGGER fail AFTER INSERT ON feedback BEGIN INSERT INTO audit VALUES (99); END;''')
    before = repository.restore_saved_application_state()
    with pytest.raises(RepositoryError):
        repository.StorePlanData({'coursework_id': course['id'], 'name': 'New'}, [task()], [{'suggestion': 'New'}])
    assert repository.restore_saved_application_state() == before


def test_csv_rollback_and_mixed_import(application):
    repository, service = application
    result = service.import_coursework_csv(io.StringIO('course,item_name,due_date\nC,A,2026-10-26\nC,,bad\nC,A,2026-10-26\n'))
    assert (result['accepted_count'], result['rejected_count']) == (1, 2)
    before = repository.restore_saved_application_state()
    with sqlite3.connect(repository.database_path) as connection:
        connection.execute("CREATE TRIGGER fail BEFORE INSERT ON coursework WHEN NEW.item_name='Fail' BEGIN SELECT RAISE(ABORT,'injected failure'); END")
    result = service.import_coursework_csv(io.StringIO('course,item_name,due_date\nC,B,2026-10-26\nC,Fail,2026-10-26\n'))
    assert not result['success'] and result['accepted_count'] == 0
    assert repository.restore_saved_application_state() == before


def test_feedback_rejection_alone_does_not_revise_plan_or_tasks(application):
    repository, service = application
    saved = repository.StorePlanData({'coursework_id': create(service)['id'], 'name': 'A'}, [task()], [{'suggestion': 'Change everything'}])
    feedback = [{**saved['feedback'][0], 'decision': 'reject'}]
    updated = repository.StorePlanData(saved['plan'], None, feedback)
    assert updated['plan'] == saved['plan'] and updated['tasks'] == saved['tasks']
    assert updated['feedback'][0]['decision'] == 'reject'


def test_legacy_or_newer_schema_is_not_changed(tmp_path):
    for version in [0, 99]:
        path = tmp_path / f'{version}.sqlite3'
        with sqlite3.connect(path) as connection:
            connection.execute('CREATE TABLE records (id INTEGER PRIMARY KEY, score REAL NOT NULL)')
            connection.execute('INSERT INTO records VALUES (7, 92)')
            connection.execute(f'PRAGMA user_version={version}')
        with pytest.raises(RepositoryError): open_application(path)
        with sqlite3.connect(path) as connection:
            assert connection.execute('SELECT * FROM records').fetchall() == [(7,92)]
            assert connection.execute('PRAGMA user_version').fetchone()[0] == version


def test_storage_timing_three_runs(application):
    repository, service = application
    saved = repository.StorePlanData({'coursework_id': create(service)['id'], 'name': 'Timing'}, [task()], [])
    for run in range(3):
        start = perf_counter()
        assert repository.get_plan(saved['plan']['id']) == saved
        display_read = perf_counter() - start
        start = perf_counter()
        saved = repository.StorePlanData({**saved['plan'], 'notes': f'Revision {run}'}, saved['tasks'], saved['feedback'])
        save_time = perf_counter() - start
        print(f'C13 repository run {run+1}: read={display_read:.6f}s save_commit={save_time:.6f}s')
        assert display_read < 2 and save_time < 2
