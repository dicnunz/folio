"""CSE-20 service checks; these do not claim UI acceptance coverage."""
import csv
import io
import platform
import sqlite3
from datetime import date
from time import perf_counter

import pytest

from src.coursework import parse_csv, validate_and_deduplicate, validate_coursework
from src.coursework_service import CourseworkService
from src.csv_storage import SQLiteCourseworkRepository, get_all_records


def record(**changes):
    return dict(course="Calculus", item_name="Review", due_date="2026-10-20", **changes)


def csv_input(rows, fields=("course", "item_name", "due_date", "score")):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    stream.seek(0)
    return stream


@pytest.fixture
def service(tmp_path):
    # This fixture explicitly has no plan/task tables or external relationships.
    return CourseworkService(SQLiteCourseworkRepository(
        tmp_path / "test.db", dependency_checker=lambda connection, record_id: []))


def stored(service):
    return get_all_records(service.repository.database_path)


def test_c1_create_edit_reopen_delete(service):
    created = service.create_coursework(record(score=" 92.5 "))
    assert created["success"]
    original = created["record"]
    assert original["source"] == "manual" and original["score"] == 92.5
    edited = service.edit_coursework(original["id"], {"item_name": " New ", "due_date": date(2026, 10, 30)})
    assert edited["success"]
    assert edited["record"]["id"] == original["id"]
    assert stored(service)[0]["item_name"] == "New"
    second = service.create_coursework({**record(), "item_name": "Second"})["record"]
    assert second["score"] is None
    assert service.delete_coursework(original["id"])["success"]
    assert stored(service) == [second]


@pytest.mark.parametrize("changes,fields", [
    ({"course": ""}, {"course"}), ({"item_name": "  "}, {"item_name"}),
    ({"due_date": None}, {"due_date"}), ({"due_date": "10/20/2026"}, {"due_date"}),
    ({"due_date": "2026-02-30"}, {"due_date"}), ({"due_date": "20261020"}, {"due_date"}),
    ({"course": " ", "item_name": "", "due_date": "bad", "score": "oops"},
     {"course", "item_name", "due_date", "score"}),
    ({"course": 42, "item_name": []}, {"course", "item_name"}),
    ({"score": "NaN"}, {"score"}), ({"score": "inf"}, {"score"}),
    ({"score": True}, {"score"}),
])
def test_c2_all_errors_and_failed_edit_preserves_original(service, changes, fields):
    original = service.create_coursework(record())["record"]
    invalid = {**record(), **changes}
    result = service.create_coursework(invalid)
    assert not result["success"]
    assert {error["field"] for error in result["errors"]} == fields
    edit = service.edit_coursework(original["id"], changes)
    assert not edit["success"]
    assert {error["field"] for error in edit["errors"]} == fields
    assert stored(service) == [original]


def test_c3_valid_csv_quoted_comma_optional_score_and_sources(service):
    rows = [{**record(), "item_name": name} for name in ["Read, review", "Assessment", "Deadline"]]
    result = service.import_coursework_csv(csv_input(rows), source="upload.csv")
    assert result["success"]
    assert (result["accepted_count"], result["rejected_count"]) == (3, 0)
    assert result["source"] == "upload.csv"
    assert [row["item_name"] for row in stored(service)] == [row["item_name"] for row in rows]
    assert all(row["source"] == "csv" for row in stored(service))


def test_c4_mixed_rows_all_errors_and_counts(service):
    rows = [{**record(), "item_name": str(i)} for i in range(3)]
    rows += [{**record(), "course": ""}, {**record(), "due_date": "bad", "score": "bad"}]
    result = service.import_coursework_csv(csv_input(rows))
    assert result["success"]
    assert (result["total_rows"], result["accepted_count"], result["rejected_count"]) == (5, 3, 2)
    assert [row["row_number"] for row in result["errors"]] == [5, 6]
    assert len(result["errors"][1]["field_errors"]) == 2
    assert len(stored(service)) == 3


@pytest.mark.parametrize("text", ["", "course\nCalculus\n",
    'course,item_name,due_date\nCalculus,Valid,2026-10-20\n"unclosed',
    'course,item_name,due_date,course\n', 'course,item_name,due_date,unknown\n'])
def test_c5_file_failure_preserves_data(service, text):
    original = service.create_coursework(record())["record"]
    result = service.import_coursework_csv(io.StringIO(text))
    assert not result["success"] and result["file_errors"]
    assert result["accepted_count"] == 0
    assert stored(service) == [original]


def test_unreadable_and_bad_encoding(service, tmp_path):
    for source in [tmp_path / "absent.csv", io.BytesIO(b'\xff')]:
        result = service.import_coursework_csv(source)
        assert result["file_errors"] and result["accepted_count"] == 0


def test_header_only_and_all_invalid(service):
    empty = service.import_coursework_csv(csv_input([]))
    assert empty["success"] and empty["total_rows"] == empty["accepted_count"] == 0
    invalid = service.import_coursework_csv(csv_input([{"course": ""}, {"course": ""}]))
    assert invalid["accepted_count"] == 0 and invalid["rejected_count"] == 2
    assert len(invalid["errors"][0]["field_errors"]) == 3
    assert stored(service) == []


def test_c5_multiple_duplicate_groups_existing_records_and_score(service):
    first = record(score=10)
    second = {**record(), "item_name": "Second"}
    rows = [first, {**first, "score": 20}, second, second, second]
    result = service.import_coursework_csv(csv_input(rows))
    assert (result["accepted_count"], result["rejected_count"], result["duplicate_rows"]) == (2, 3, 3)
    assert [row["row_number"] for row in result["errors"]] == [3, 5, 6]
    repeated = service.import_coursework_csv(csv_input(rows))
    assert repeated["accepted_count"] == 0 and repeated["duplicate_rows"] == 5
    assert len(stored(service)) == 2
    assert not service.create_coursework(first)["success"]
    assert not service.edit_coursework(stored(service)[1]["id"], {"item_name": "Review"})["success"]


def test_parser_locations_bom_binary_and_caller_stream():
    stream = io.BytesIO(b'\xef\xbb\xbfcourse,item_name,due_date\r\n\r\nCalculus,"line one\r\nline two",2026-10-20\r\nCalculus,,bad\r\n')
    result = parse_csv(stream, source="named.csv")
    assert not stream.closed
    assert not result["file_errors"]
    assert [(row["row_number"], row["end_row_number"]) for row in result["rows"]] == [(3, 4), (5, 5)]
    classified = validate_and_deduplicate(result["rows"])
    assert classified["rejected"][0]["source"] == "named.csv"
    assert classified["rejected"][0]["row_number"] == 5


def test_extra_values_are_row_errors(service):
    result = service.import_coursework_csv(io.StringIO('course,item_name,due_date\nC,A,2026-10-20,extra\nC,B,2026-10-21\n'))
    assert result["accepted_count"] == result["invalid_rows"] == 1
    assert result["errors"][0]["field_errors"][0]["code"] == "columns"


@pytest.mark.parametrize("dependencies,code", [(None, "relationships_unknown"), (["plan:1"], "dependent_records"), (["task:1"], "dependent_records")])
def test_deletion_requires_relationship_check(service, dependencies, code):
    original = service.create_coursework(record())["record"]
    service.repository.dependency_checker = lambda connection, record_id: dependencies
    result = service.delete_coursework(original["id"])
    assert result["errors"][0]["code"] == code
    assert stored(service) == [original]


def test_not_found_and_immutable_identifiers(service):
    assert service.edit_coursework(999, {})["errors"][0]["code"] == "not_found"
    assert service.delete_coursework(999)["errors"][0]["code"] == "not_found"
    original = service.create_coursework(record())["record"]
    assert not service.edit_coursework(original["id"], {"id": 999, "source": "changed"})["success"]
    assert stored(service) == [original]


def test_sqlite_foreign_keys_preserve_dependents_even_if_checker_wrong(service):
    original = service.create_coursework(record())["record"]
    with sqlite3.connect(service.repository.database_path) as connection:
        connection.execute('CREATE TABLE plans (coursework_id INTEGER REFERENCES records(id))')
        connection.execute('INSERT INTO plans VALUES (?)', (original["id"],))
    result = service.delete_coursework(original["id"])
    assert result["errors"][0]["code"] == "storage"
    assert stored(service) == [original]
    with sqlite3.connect(service.repository.database_path) as connection:
        assert connection.execute('SELECT * FROM plans').fetchall() == [(original["id"],)]


@pytest.mark.parametrize("operation", ["INSERT", "UPDATE", "DELETE"])
def test_repository_write_failures_roll_back(service, operation):
    original = service.create_coursework(record())["record"]
    with sqlite3.connect(service.repository.database_path) as connection:
        connection.execute(f"CREATE TRIGGER fail BEFORE {operation} ON records BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    if operation == "INSERT":
        result = service.create_coursework({**record(), "item_name": "Another"})
    elif operation == "UPDATE":
        result = service.edit_coursework(original["id"], {"item_name": "Changed"})
    else:
        result = service.delete_coursework(original["id"])
    assert not result["success"] and result["errors"][0]["code"] == "storage"
    assert stored(service) == [original]


def test_import_rolls_back_valid_prefix_on_storage_failure(service):
    original = service.create_coursework(record())["record"]
    with sqlite3.connect(service.repository.database_path) as connection:
        connection.execute("CREATE TRIGGER fail BEFORE INSERT ON records WHEN NEW.item_name = 'Fail' BEGIN SELECT RAISE(ABORT, 'injected failure'); END")
    result = service.import_coursework_csv(csv_input([{**record(), "item_name": name} for name in ["Saved then rolled back", "Fail"]]))
    assert not result["success"] and result["storage_errors"]
    assert result["accepted_count"] == result["inserted_rows"] == 0
    assert result["rejected_count"] == 2 and result["records"] == []
    assert [row["row_number"] for row in result["errors"]] == [2, 3]
    assert stored(service) == [original]


def test_legacy_nonnullable_score_is_not_silently_migrated(service):
    with sqlite3.connect(service.repository.database_path) as connection:
        connection.execute('CREATE TABLE records (id INTEGER PRIMARY KEY, course TEXT, item_name TEXT, due_date TEXT, score REAL NOT NULL, source TEXT)')
    original = service.create_coursework(record(score=5))["record"]
    result = service.create_coursework({**record(), "item_name": "No score"})
    assert not result["success"] and result["errors"][0]["code"] == "storage"
    assert stored(service) == [original]


def test_p7_service_import_500_three_runs(tmp_path):
    print(f"\nP7 service benchmark: {platform.platform()}, Python {platform.python_version()}, SQLite {sqlite3.sqlite_version}")
    for run in range(3):
        path = tmp_path / f"performance-{run}.db"
        service = CourseworkService(SQLiteCourseworkRepository(path))
        stream = csv_input([{**record(score=i % 101), "item_name": f"Assignment {i}"} for i in range(500)])
        start = perf_counter()
        result = service.import_coursework_csv(stream)
        elapsed = perf_counter() - start
        assert result["success"] and result["accepted_count"] == 500 and result["rejected_count"] == 0
        assert len(stored(service)) == 500
        print(f"run {run + 1}: {elapsed:.6f}s, accepted=500, rejected=0, database={path.stat().st_size} bytes")
        assert elapsed < 5


def test_commit_failure_rolls_back_import(service):
    original = service.create_coursework(record())["record"]
    with sqlite3.connect(service.repository.database_path) as connection:
        connection.executescript('''
            CREATE TABLE parent (id INTEGER PRIMARY KEY);
            CREATE TABLE audit (parent_id INTEGER REFERENCES parent(id)
                                DEFERRABLE INITIALLY DEFERRED);
            CREATE TRIGGER audit_import AFTER INSERT ON records
            BEGIN INSERT INTO audit VALUES (999); END;
        ''')
    result = service.import_coursework_csv(csv_input([{**record(), "item_name": "New"}]))
    assert not result["success"] and result["storage_errors"]
    assert result["records"] == [] and result["accepted_count"] == 0
    assert result["rejected_count"] == 1
    assert stored(service) == [original]
    with sqlite3.connect(service.repository.database_path) as connection:
        assert connection.execute('SELECT * FROM audit').fetchall() == []
