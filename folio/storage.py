"""SQLite academic repositories. Domain decisions belong to application services.

StorePlanData saves an explicitly supplied plan aggregate atomically. Child lists
are complete replacements when supplied; None leaves that collection unchanged.
Existing child IDs must belong to this plan. Omitted child IDs request new rows.
"""
from contextlib import contextmanager
from pathlib import Path
import sqlite3

from demos.src.coursework_service import RepositoryError
from demos.src.scheduling import parse_task_time

from .deadlines import validate_preparation

SCHEMA_VERSION = 4
PREPARATION_CONTEXT = """SELECT c.id, c.item_name, c.due_date, d.cutoff
    FROM coursework c LEFT JOIN preparation_cutoffs d ON d.coursework_id=c.id"""
SCHEMA = (
    """CREATE TABLE coursework (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL, item_name TEXT NOT NULL, due_date TEXT NOT NULL,
        score REAL, source TEXT NOT NULL,
        UNIQUE(course, item_name, due_date))""",
    """CREATE TABLE plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        coursework_id INTEGER NOT NULL REFERENCES coursework(id) ON DELETE RESTRICT,
        name TEXT NOT NULL, template_id TEXT, notes TEXT NOT NULL DEFAULT '',
        active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)))""",
    """CREATE TABLE tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
        name TEXT NOT NULL, start_time TEXT NOT NULL, end_time TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)),
        CHECK(start_time < end_time))""",
    """CREATE TABLE feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
        suggestion TEXT NOT NULL, decision TEXT CHECK(decision IN ('accept','reject','adapt')),
        adapted_text TEXT)""",
    "CREATE INDEX plans_coursework ON plans(coursework_id)",
    "CREATE INDEX tasks_plan ON tasks(plan_id)",
    "CREATE INDEX feedback_plan ON feedback(plan_id)",
)


class AcademicRepository:
    def __init__(self, database_path):
        self.database_path = Path(database_path)

    def _connect(self):
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self):
        """Create only a fresh versioned application DB; never overwrite a demo DB."""
        connection = None
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                if tables:
                    raise RepositoryError("Unversioned database: choose a new application database; legacy demo data has not been changed.")
                for statement in SCHEMA:
                    connection.execute(statement)
                version = 1
            if version == 1:
                # Additive, transactional migration preserves IDs and all relationships.
                connection.execute("ALTER TABLE coursework ADD COLUMN start_time TEXT")
                connection.execute("""ALTER TABLE coursework ADD COLUMN end_time TEXT
                    CHECK ((start_time IS NULL AND end_time IS NULL) OR
                           (start_time IS NOT NULL AND end_time IS NOT NULL AND start_time < end_time))""")
                version = 2
            if version == 2:
                connection.execute("ALTER TABLE tasks ADD COLUMN preparation INTEGER NOT NULL DEFAULT 0 CHECK(preparation IN (0,1))")
                connection.execute("""CREATE TABLE reminders (
                    task_id INTEGER PRIMARY KEY REFERENCES tasks(id) ON DELETE CASCADE,
                    remind_at TEXT, revision INTEGER NOT NULL,
                    delivered INTEGER NOT NULL DEFAULT 0 CHECK(delivered IN (0,1)))""")
                version = 3
            if version == 3:
                connection.execute("""CREATE TABLE preparation_cutoffs (
                    coursework_id INTEGER PRIMARY KEY REFERENCES coursework(id) ON DELETE CASCADE,
                    cutoff TEXT NOT NULL)""")
                connection.execute("ALTER TABLE reminders ADD COLUMN needs_review INTEGER NOT NULL DEFAULT 0 CHECK(needs_review IN (0,1))")
                connection.execute("""CREATE TRIGGER reminder_time_changed
                    AFTER UPDATE OF start_time,end_time ON tasks
                    WHEN OLD.start_time != NEW.start_time OR OLD.end_time != NEW.end_time
                    BEGIN UPDATE reminders SET needs_review=1,revision=revision+1
                    WHERE task_id=NEW.id AND remind_at IS NOT NULL; END""")
                connection.execute("""CREATE TRIGGER reminder_task_completed
                    AFTER UPDATE OF completed ON tasks WHEN NEW.completed=1 AND OLD.completed=0
                    BEGIN UPDATE reminders SET remind_at=NULL,needs_review=0,revision=revision+1,delivered=0
                    WHERE task_id=NEW.id AND remind_at IS NOT NULL AND delivered=0; END""")
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            elif version != SCHEMA_VERSION:
                raise RepositoryError(f"Unsupported database version {version}; expected {SCHEMA_VERSION}.")
            connection.commit()
        except (sqlite3.Error, OSError) as error:
            raise RepositoryError(f"Cannot initialize academic storage: {error}") from error
        finally:
            if connection is not None:
                connection.close()  # Also rolls back an incomplete initialization.

    @contextmanager
    def transaction(self):
        connection = None
        try:
            connection = self._connect()
            connection.execute("BEGIN IMMEDIATE")
            yield CourseworkTransaction(connection)
            connection.commit()
        except sqlite3.Error as error:
            raise RepositoryError(f"Academic storage failed: {error}") from error
        finally:
            if connection is not None:
                connection.close()  # Roll back any exception, including commit failure.

    def store_coursework(self, action, record):
        """Persist already-validated coursework; use CourseworkService for UI input."""
        with self.transaction() as transaction:
            if action == "CREATE":
                saved = transaction.insert(record, record.get("source", "manual"))
            elif action == "UPDATE":
                saved = transaction.update(record["id"], record)
            elif action == "DELETE":
                saved = transaction.get(record["id"])
                if saved is None:
                    raise RepositoryError("Coursework was not found.")
                if transaction.dependencies(record["id"]):
                    raise RepositoryError("Coursework is referenced by a plan; deletion was not performed.")
                transaction.delete(record["id"])
            else:
                raise RepositoryError("Unknown coursework storage action.")
        return saved

    def preparation_contexts(self):
        with self._read_snapshot() as connection:
            return {row["id"]: dict(row) for row in connection.execute(PREPARATION_CONTEXT)}

    def set_preparation_cutoff(self, coursework_id, value):
        cutoff = parse_task_time(value.strip()).isoformat(timespec="minutes") if value and value.strip() else None
        with self.transaction() as tx:
            if tx.get(coursework_id) is None:
                raise RepositoryError("Coursework was not found.")
            if cutoff is None:
                tx.connection.execute("DELETE FROM preparation_cutoffs WHERE coursework_id=?", (coursework_id,))
            else:
                tx.connection.execute("""INSERT INTO preparation_cutoffs(coursework_id,cutoff) VALUES (?,?)
                    ON CONFLICT(coursework_id) DO UPDATE SET cutoff=excluded.cutoff""", (coursework_id, cutoff))

    def store_plan_data(self, plan, tasks=None, feedback=None):
        """Save a validated student-approved aggregate, returning saved IDs after commit.

        This does not accept/reject suggestions or generate/revise planning tasks.
        An existing plan cannot be reassigned to another coursework record.
        """
        with self.transaction() as transaction:
            connection = transaction.connection
            plan_id = plan.get("id")
            values = (plan["coursework_id"], plan["name"], plan.get("template_id"),
                      plan.get("notes", ""), plan.get("active", True))
            if plan_id is None:
                plan_id = connection.execute(
                    "INSERT INTO plans(coursework_id,name,template_id,notes,active) VALUES (?,?,?,?,?)", values).lastrowid
            else:
                original = connection.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
                if original is None:
                    raise RepositoryError("Plan was not found.")
                if original["coursework_id"] != plan["coursework_id"]:
                    raise RepositoryError("A saved plan's coursework association cannot be reassigned.")
                connection.execute("UPDATE plans SET coursework_id=?,name=?,template_id=?,notes=?,active=? WHERE id=?", (*values, plan_id))
            if tasks is not None:
                coursework = transaction.preparation_context(plan["coursework_id"])
                prior = {t["id"]: t for t in connection.execute("SELECT * FROM tasks WHERE plan_id=?", (plan_id,))}
                for task in tasks:
                    old = prior.get(task.get("id"))
                    candidate = {**(dict(old) if old else {}), **task}
                    if candidate.get("preparation") and (not old or not old["preparation"] or any(
                            candidate[key] != old[key] for key in ("start_time", "end_time"))):
                        validate_preparation(candidate, coursework)
                self._save_children(connection, "tasks", plan_id, tasks,
                                    ("name", "start_time", "end_time", "completed", "preparation"),
                                    {"completed": False, "preparation": False})
            if feedback is not None:
                self._save_children(connection, "feedback", plan_id, feedback,
                                    ("suggestion", "decision", "adapted_text"), {"decision": None, "adapted_text": None})
            saved = self._get_plan(connection, plan_id)
        return saved

    def delete_plan(self, plan_id):
        """Explicitly delete a plan and its owned tasks/feedback in one transaction.

        Coursework and every other plan are preserved. This is an aggregate
        deletion API for the plan owner, not implicit coursework cascading.
        """
        with self.transaction() as transaction:
            connection = transaction.connection
            if connection.execute("SELECT id FROM plans WHERE id=?", (plan_id,)).fetchone() is None:
                raise RepositoryError("Plan was not found.")
            connection.execute("DELETE FROM feedback WHERE plan_id=?", (plan_id,))
            connection.execute("DELETE FROM tasks WHERE plan_id=?", (plan_id,))
            connection.execute("DELETE FROM plans WHERE id=?", (plan_id,))

    @staticmethod
    def _save_children(connection, table, plan_id, records, fields, defaults):
        # table/fields are internal constants, never supplied by the caller.
        original_ids = {row[0] for row in connection.execute(f"SELECT id FROM {table} WHERE plan_id=?", (plan_id,))}
        kept = set()
        for record in records:
            if record.get("plan_id", plan_id) != plan_id:
                raise RepositoryError(f"{table} association does not match the saved plan.")
            values = [record.get(field, defaults.get(field)) for field in fields]
            record_id = record.get("id")
            if record_id is None:
                columns = ','.join(fields)
                parameters = ','.join('?' for _ in fields)
                record_id = connection.execute(
                    f"INSERT INTO {table}(plan_id,{columns}) VALUES (?,{parameters})", (plan_id, *values)).lastrowid
            else:
                if record_id not in original_ids or record_id in kept:
                    raise RepositoryError(f"Unknown, repeated, or foreign {table} ID: {record_id}.")
                updates = [(field, value) for field, value in zip(fields, values)
                           if not (table == "tasks" and field in ("completed", "preparation") and field not in record)]
                assignments = ','.join(f'{field}=?' for field, _ in updates)
                connection.execute(f"UPDATE {table} SET {assignments} WHERE id=? AND plan_id=?",
                                   (*(value for _, value in updates), record_id, plan_id))
            kept.add(record_id)
        for record_id in original_ids - kept:
            connection.execute(f"DELETE FROM {table} WHERE id=? AND plan_id=?", (record_id, plan_id))

    @staticmethod
    def _get_plan(connection, plan_id):
        row = connection.execute("SELECT * FROM plans WHERE id=?", (plan_id,)).fetchone()
        if row is None:
            return None
        return {"plan": dict(row),
                "tasks": [dict(row) for row in connection.execute("SELECT * FROM tasks WHERE plan_id=? ORDER BY id", (plan_id,))],
                "feedback": [dict(row) for row in connection.execute("SELECT * FROM feedback WHERE plan_id=? ORDER BY id", (plan_id,))]}

    def get_plan(self, plan_id):
        with self._read_snapshot() as connection:
            return self._get_plan(connection, plan_id)

    @contextmanager
    def _read_snapshot(self):
        connection = None
        try:
            connection = self._connect()
            connection.execute("BEGIN")
            yield connection
        except sqlite3.Error as error:
            raise RepositoryError(f"Cannot restore academic state: {error}") from error
        finally:
            if connection is not None:
                connection.close()

    def restore_saved_application_state(self):
        """Read a consistent academic-only snapshot; never seed or append records."""
        with self._read_snapshot() as connection:
            return {table: [dict(row) for row in connection.execute(f"SELECT * FROM {table} ORDER BY id")]
                    for table in ("coursework", "plans", "tasks", "feedback")}

    # Names specified in the M1 Design; snake_case is used internally.
    StoreCoursework = store_coursework
    StorePlanData = store_plan_data
    RestoreSavedApplicationState = restore_saved_application_state


class CourseworkTransaction:
    """Implements the repository contract already consumed by CSE-20."""
    def __init__(self, connection):
        self.connection = connection

    def academic_state(self):
        """Snapshot inside the current transaction for scheduling decisions."""
        return {table: [dict(row) for row in self.connection.execute(f"SELECT * FROM {table} ORDER BY id")]
                for table in ("coursework", "plans", "tasks", "feedback")}

    def preparation_context(self, coursework_id):
        row = self.connection.execute(PREPARATION_CONTEXT + " WHERE c.id=?", (coursework_id,)).fetchone()
        return dict(row) if row else None

    def update_task_times(self, task_id, start_time, end_time):
        task = self.connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if task:
            item = self.connection.execute(
                PREPARATION_CONTEXT + " JOIN plans p ON c.id=p.coursework_id WHERE p.id=?", (task["plan_id"],)).fetchone()
            if (task["start_time"], task["end_time"]) != (start_time, end_time):
                validate_preparation({**dict(task), "start_time": start_time, "end_time": end_time}, dict(item))
        cursor = self.connection.execute(
            "UPDATE tasks SET start_time=?,end_time=? WHERE id=?", (start_time, end_time, task_id))
        if cursor.rowcount != 1:
            raise RepositoryError("Task was not found.")
        return dict(self.connection.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())

    def list_records(self):
        return [dict(row) for row in self.connection.execute("SELECT * FROM coursework ORDER BY id")]

    def get(self, record_id):
        row = self.connection.execute("SELECT * FROM coursework WHERE id=?", (record_id,)).fetchone()
        return dict(row) if row else None

    def insert(self, record, source):
        record_id = self.connection.execute(
            "INSERT INTO coursework(course,item_name,due_date,score,source,start_time,end_time) VALUES (?,?,?,?,?,?,?)",
            (record["course"], record["item_name"], record["due_date"], record.get("score"), source, record.get("start_time"), record.get("end_time"))).lastrowid
        return self.get(record_id)

    def update(self, record_id, record):
        cursor = self.connection.execute(
            "UPDATE coursework SET course=?,item_name=?,due_date=?,score=?,start_time=?,end_time=? WHERE id=?",
            (record["course"], record["item_name"], record["due_date"], record.get("score"), record.get("start_time"), record.get("end_time"), record_id))
        if cursor.rowcount != 1:
            raise RepositoryError("Coursework was not found.")
        return self.get(record_id)

    def dependencies(self, record_id):
        # Tasks/feedback reach coursework via their parent plan (no redundant FK).
        return [dict(row) for row in self.connection.execute("SELECT id,name FROM plans WHERE coursework_id=?", (record_id,))]

    def delete(self, record_id):
        self.connection.execute("DELETE FROM coursework WHERE id=?", (record_id,))
