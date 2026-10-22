"""CSV validation and SQLite persistence for the Folio prototype."""

import sqlite3
from contextlib import closing, contextmanager

from .coursework import (REQUIRED_COLUMNS as COURSEWORK_REQUIRED_COLUMNS, normalize_row, parse_csv,
                         validate_coursework, validate_and_deduplicate)
from .coursework_service import CourseworkService, RepositoryError


# Legacy CSV writer field list; score is now optional during validation.
REQUIRED_COLUMNS = COURSEWORK_REQUIRED_COLUMNS + ("score",)


def initialize_database(database_path):
    """Create the Folio records table when it does not already exist."""
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                item_name TEXT NOT NULL,
                due_date TEXT NOT NULL,
                score REAL,
                source TEXT NOT NULL,
                UNIQUE(course, item_name, due_date, score)
            )
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(records)")}
        for field in ("start_time", "end_time"):
            if field not in columns:
                connection.execute(f"ALTER TABLE records ADD COLUMN {field} TEXT")


def read_csv(csv_path):
    """Compatibility reader; file errors continue to raise ValueError."""
    result = parse_csv(csv_path)
    if result["file_errors"]:
        raise ValueError("; ".join(result["file_errors"]))
    return [row["record"] for row in result["rows"]]


def validate_row(row):
    """Compatibility wrapper returning messages from the shared validator."""
    return [error["message"] for error in validate_coursework(row)["errors"]]


def is_duplicate(connection, row):
    """Return whether an identical record already exists."""
    match = connection.execute(
        """
        SELECT 1
        FROM records
        WHERE course = ? AND item_name = ? AND due_date = ?
        LIMIT 1
        """,
        (row["course"], row["item_name"], row["due_date"]),
    ).fetchone()
    return match is not None


def insert_row(connection, row, source="csv"):
    """Insert one validated row and return its database ID."""
    cursor = connection.execute(
        """
        INSERT INTO records (course, item_name, due_date, score, source, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row["course"],
            row["item_name"],
            row["due_date"],
            row["score"],
            source,
            row.get("start_time"),
            row.get("end_time"),
        ),
    )
    return cursor.lastrowid


def import_csv(csv_path, database_path):
    """Import through the shared service, retaining legacy summary keys."""
    return CourseworkService(SQLiteCourseworkRepository(database_path)).import_coursework_csv(csv_path)


def get_all_records(database_path):
    """Return all stored records as dictionaries in insertion order."""
    initialize_database(database_path)
    with closing(sqlite3.connect(database_path)) as connection, connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, course, item_name, due_date, score, source, start_time, end_time
            FROM records
            ORDER BY id
            """
        ).fetchall()
    return [dict(row) for row in rows]


class SQLiteCourseworkRepository:
    """Adapter for the existing prototype, not the unfinished CSE-22 repository.

    dependency_checker(connection, id) must return references or an empty list.
    Without it, deletion fails closed.
    """

    def __init__(self, database_path, dependency_checker=None):
        self.database_path = database_path
        self.dependency_checker = dependency_checker

    @contextmanager
    def transaction(self):
        connection = None
        
        try:
            initialize_database(self.database_path)
            connection = sqlite3.connect(self.database_path)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("BEGIN IMMEDIATE")
            yield _SQLiteTransaction(connection, self.dependency_checker)
            connection.commit()
            
        except sqlite3.Error as error:
            if connection is not None:
                connection.rollback()
            raise RepositoryError(f"Coursework storage failed: {error}") from error
        
        except Exception:
            if connection is not None:
                connection.rollback()
            raise
        
        finally:
            if connection is not None:
                connection.close()


class _SQLiteTransaction: # pylint: disable=too-few-public-methods
    """Transaction context for SQLiteCourseworkRepository."""
    def __init__(self, connection, dependency_checker):
        self.connection = connection
        self.dependency_checker = dependency_checker

    def list_records(self):
        return [dict(row) for row in self.connection.execute("SELECT * FROM records ORDER BY id")]

    def get(self, record_id):
        row = self.connection.execute("SELECT * FROM records WHERE id = ?", (record_id,)).fetchone()
        return dict(row) if row is not None else None

    def insert(self, record, source):
        return self.get(insert_row(self.connection, record, source))

    def update(self, record_id, record):
        self.connection.execute(
            "UPDATE records SET course=?, item_name=?, due_date=?, score=?, start_time=?, end_time=? WHERE id=?",
            (record["course"], record["item_name"], record["due_date"], record["score"], record.get("start_time"), record.get("end_time"), record_id))
        return self.get(record_id)

    def dependencies(self, record_id):
        if self.dependency_checker is None:
            return None
        return self.dependency_checker(self.connection, record_id)

    def delete(self, record_id):
        self.connection.execute("DELETE FROM records WHERE id=?", (record_id,))
