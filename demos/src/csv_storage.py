"""CSV validation and SQLite persistence for the Folio prototype."""

import csv
import sqlite3
from datetime import date


REQUIRED_COLUMNS = ("course", "item_name", "due_date", "score")


def initialize_database(database_path):
    """Create the Folio records table when it does not already exist."""
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                item_name TEXT NOT NULL,
                due_date TEXT NOT NULL,
                score REAL NOT NULL,
                source TEXT NOT NULL,
                UNIQUE(course, item_name, due_date, score)
            )
            """
        )


def read_csv(csv_path):
    """Read a CSV file and verify that all required columns are present."""
    with open(csv_path, newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = set(REQUIRED_COLUMNS) - fieldnames
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"CSV is missing required columns: {missing}")
        return list(reader)


def normalize_row(row):
    """Trim text and normalize valid dates and numeric scores."""
    normalized = {
        key: value.strip() if isinstance(value, str) else value
        for key, value in row.items()
    }

    due_date = normalized.get("due_date")
    if due_date:
        try:
            normalized["due_date"] = date.fromisoformat(due_date).isoformat()
        except (TypeError, ValueError):
            pass

    score = normalized.get("score")
    if score not in (None, ""):
        try:
            normalized["score"] = float(score)
        except (TypeError, ValueError):
            pass

    return normalized


def validate_row(row):
    """Return validation errors for a normalized CSV row."""
    errors = []

    if None in row:
        errors.append("Row contains more values than the CSV header.")

    for field in REQUIRED_COLUMNS:
        if row.get(field) in (None, ""):
            errors.append(f"{field} is required.")

    due_date = row.get("due_date")
    if due_date not in (None, ""):
        try:
            date.fromisoformat(due_date)
        except (TypeError, ValueError):
            errors.append("due_date must use YYYY-MM-DD format.")

    score = row.get("score")
    if score not in (None, ""):
        try:
            float(score)
        except (TypeError, ValueError):
            errors.append("score must be numeric.")

    return errors


def is_duplicate(connection, row):
    """Return whether an identical record already exists."""
    match = connection.execute(
        """
        SELECT 1
        FROM records
        WHERE course = ? AND item_name = ? AND due_date = ? AND score = ?
        LIMIT 1
        """,
        (row["course"], row["item_name"], row["due_date"], row["score"]),
    ).fetchone()
    return match is not None


def insert_row(connection, row, source="csv"):
    """Insert one validated row and return its database ID."""
    cursor = connection.execute(
        """
        INSERT INTO records (course, item_name, due_date, score, source)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            row["course"],
            row["item_name"],
            row["due_date"],
            row["score"],
            source,
        ),
    )
    return cursor.lastrowid


def import_csv(csv_path, database_path):
    """Import valid, nonduplicate CSV rows and return an import summary."""
    initialize_database(database_path)
    rows = read_csv(csv_path)
    summary = {
        "total_rows": len(rows),
        "inserted_rows": 0,
        "invalid_rows": 0,
        "duplicate_rows": 0,
        "errors": [],
    }

    with sqlite3.connect(database_path) as connection:
        for row_number, row in enumerate(rows, start=2):
            normalized = normalize_row(row)
            errors = validate_row(normalized)

            if errors:
                summary["invalid_rows"] += 1
                summary["errors"].append(
                    {"row_number": row_number, "errors": errors}
                )
                continue

            if is_duplicate(connection, normalized):
                summary["duplicate_rows"] += 1
                continue

            insert_row(connection, normalized)
            summary["inserted_rows"] += 1

    return summary


def get_all_records(database_path):
    """Return all stored records as dictionaries in insertion order."""
    initialize_database(database_path)
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, course, item_name, due_date, score, source
            FROM records
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]
