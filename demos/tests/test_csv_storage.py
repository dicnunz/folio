import csv
import sqlite3

from src import csv_storage


def write_csv(path, rows, fieldnames=csv_storage.REQUIRED_COLUMNS):
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def valid_row(**changes):
    row = {
        "course": "Calculus",
        "item_name": "Chapter Review",
        "due_date": "2026-09-20",
        "score": "92",
    }
    row.update(changes)
    return row


def test_valid_row_is_normalized_and_accepted():
    row = csv_storage.normalize_row(
        valid_row(course="  Calculus  ", score=" 92.5 ")
    )

    assert csv_storage.validate_row(row) == []
    assert row["course"] == "Calculus"
    assert row["score"] == 92.5


def test_missing_required_fields_are_rejected():
    row = csv_storage.normalize_row(valid_row(course="", item_name="   "))

    errors = csv_storage.validate_row(row)

    assert "course is required." in errors
    assert "item_name is required." in errors


def test_malformed_values_are_rejected():
    row = csv_storage.normalize_row(
        valid_row(due_date="September 20", score="excellent")
    )

    errors = csv_storage.validate_row(row)

    assert "due_date must use YYYY-MM-DD format." in errors
    assert "score must be numeric." in errors


def test_csv_missing_a_required_column_is_rejected(tmp_path):
    csv_path = tmp_path / "missing-column.csv"
    write_csv(csv_path, [{"course": "Calculus"}], fieldnames=("course",))

    try:
        csv_storage.read_csv(csv_path)
        assert False, "Expected a missing-column ValueError"
    except ValueError as error:
        assert "required columns" in str(error)


def test_valid_row_is_inserted_into_sqlite(tmp_path):
    database_path = tmp_path / "folio.db"
    csv_storage.initialize_database(database_path)
    row = csv_storage.normalize_row(valid_row())

    with sqlite3.connect(database_path) as connection:
        record_id = csv_storage.insert_row(connection, row)

    records = csv_storage.get_all_records(database_path)
    assert record_id == 1
    assert len(records) == 1
    assert records[0]["course"] == "Calculus"


def test_duplicate_csv_record_is_not_inserted_twice(tmp_path):
    csv_path = tmp_path / "duplicate.csv"
    database_path = tmp_path / "folio.db"
    row = valid_row()
    write_csv(csv_path, [row, row])

    summary = csv_storage.import_csv(csv_path, database_path)

    assert summary["inserted_rows"] == 1
    assert summary["duplicate_rows"] == 1
    assert len(csv_storage.get_all_records(database_path)) == 1


def test_mixed_import_reports_each_row_type(tmp_path):
    csv_path = tmp_path / "mixed.csv"
    database_path = tmp_path / "folio.db"
    first = valid_row()
    second = valid_row(
        course="Software Engineering",
        item_name="Design Document",
        due_date="2026-09-22",
        score="88",
    )
    invalid = valid_row(item_name="", due_date="not-a-date")
    write_csv(csv_path, [first, second, invalid, first])

    summary = csv_storage.import_csv(csv_path, database_path)

    assert summary["total_rows"] == 4
    assert summary["inserted_rows"] == 2
    assert summary["invalid_rows"] == 1
    assert summary["duplicate_rows"] == 1
    assert summary["errors"][0]["row_number"] == 4


def test_import_preserves_normalized_data_and_source(tmp_path):
    csv_path = tmp_path / "source.csv"
    database_path = tmp_path / "folio.db"
    write_csv(csv_path, [valid_row(course="  Calculus ", score="92.5")])

    csv_storage.import_csv(csv_path, database_path)
    record = csv_storage.get_all_records(database_path)[0]

    assert record["course"] == "Calculus"
    assert record["item_name"] == "Chapter Review"
    assert record["due_date"] == "2026-09-20"
    assert record["score"] == 92.5
    assert record["source"] == "csv"
