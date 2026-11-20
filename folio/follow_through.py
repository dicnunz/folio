from datetime import datetime

from demos.src.coursework_service import RepositoryError
from demos.src.scheduling import parse_task_time


class FollowThrough:
    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def _task(tx, task_id, plan_id=None):
        row = tx.connection.execute(
            """SELECT t.* FROM tasks t JOIN plans p ON p.id=t.plan_id
               WHERE t.id=? AND p.active=1""", (task_id,)).fetchone()
        if row is None or (plan_id is not None and row["plan_id"] != plan_id):
            raise RepositoryError("Task was not found in the selected active plan.")
        return row

    def set_completed(self, plan_id, task_id, completed, expected_completed):
        with self.repository.transaction() as tx:
            task = self._task(tx, task_id, plan_id)
            current = bool(task["completed"])
            if current == completed:
                return False
            if current != expected_completed:
                raise RepositoryError("Completion changed. Refresh the plan.")
            tx.connection.execute("UPDATE tasks SET completed=? WHERE id=?", (int(completed), task_id))
        return True

    def get_reminder(self, task_id):
        with self.repository._read_snapshot() as connection:
            row = connection.execute("SELECT * FROM reminders WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            return {"enabled": False, "remind_at": None, "revision": 0}
        return {"enabled": row["remind_at"] is not None and not row["needs_review"], "remind_at": row["remind_at"],
                "revision": row["revision"], "needs_review": bool(row["needs_review"])}

    def save_reminder(self, task_id, enabled, remind_at, expected_revision):
        when = None
        if enabled:
            try:
                when = parse_task_time(remind_at).isoformat(timespec="minutes")
            except (TypeError, ValueError):
                raise ValueError("Enter a valid local reminder time.") from None
        with self.repository.transaction() as tx:
            task = self._task(tx, task_id)
            if enabled and task["completed"]:
                raise ValueError("Mark this task incomplete before enabling a reminder.")
            row = tx.connection.execute("SELECT * FROM reminders WHERE task_id=?", (task_id,)).fetchone()
            revision = row["revision"] if row else 0
            if revision != expected_revision:
                raise ValueError("Reminder changed. Refresh and check the saved time.")
            if row and row["remind_at"] == when and not row["needs_review"]:
                return
            tx.connection.execute(
                """INSERT INTO reminders(task_id,remind_at,revision,delivered)
                   VALUES (?, ?, ?, 0)
                   ON CONFLICT(task_id) DO UPDATE SET
                   remind_at=excluded.remind_at,revision=excluded.revision,delivered=0,needs_review=0""",
                (task_id, when, revision + 1))

    def claim_due(self, now=None):
        cutoff = (now or datetime.now()).isoformat(timespec="minutes")
        query = """SELECT r.task_id,t.name,p.name AS plan_name,r.remind_at
                   FROM reminders r JOIN tasks t ON r.task_id=t.id
                   JOIN plans p ON t.plan_id=p.id
                   WHERE r.delivered=0 AND r.needs_review=0 AND r.remind_at<=? AND p.active=1 AND t.completed=0
                   ORDER BY r.remind_at,r.task_id"""
        with self.repository._read_snapshot() as connection:
            if not connection.execute(query + " LIMIT 1", (cutoff,)).fetchone():
                return []
        with self.repository.transaction() as tx:
            rows = tx.connection.execute(query, (cutoff,)).fetchall()
            tx.connection.executemany("UPDATE reminders SET delivered=1 WHERE task_id=?",
                                      [(row["task_id"],) for row in rows])
            return [{**dict(row), "overdue": row["remind_at"] < cutoff} for row in rows]
