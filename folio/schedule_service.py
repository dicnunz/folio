"""Application scheduling: inspect current state and save only requested times."""
from demos.src.coursework_service import RepositoryError
from demos.src.scheduling import combine_active_tasks, intervals_overlap, parse_task_time, validate_task_times


class ScheduleService:
    def __init__(self, repository):
        self.repository = repository

    def get_schedule(self):
        return combine_active_tasks(self.repository.restore_saved_application_state())

    def reschedule_task(self, task_id, start_time, end_time, expected_times=None):
        start_time = start_time.strip() if isinstance(start_time, str) else start_time
        end_time = end_time.strip() if isinstance(end_time, str) else end_time
        errors = validate_task_times(start_time, end_time)
        result = {"success": False, "record": None, "errors": errors, "conflicts": []}
        if errors:
            return result
        try:
            # Recheck all current active tasks under the same write lock as the update.
            with self.repository.transaction() as transaction:
                schedule = combine_active_tasks(transaction.academic_state())
                if schedule["errors"]:
                    result["errors"] = [{"field": "schedule", "message": "Some active tasks have invalid saved times. Correct them through the owning plan before checking a time change."}]
                    return result
                original = next((row for row in schedule["tasks"] if row["id"] == task_id), None)
                if original is None:
                    result["errors"] = [{"field": "task", "message": "Task was not found in an active plan. Refresh the schedule."}]
                    return result
                if expected_times is not None and tuple(expected_times) != (original["start_time"], original["end_time"]):
                    result["errors"] = [{"field": "task", "message": "This task changed since it was displayed. Review its current times before trying again."}]
                    return result
                start, end = parse_task_time(start_time), parse_task_time(end_time)
                result["conflicts"] = [row for row in schedule["tasks"] if row["id"] != task_id and
                    intervals_overlap(start, end, parse_task_time(row["start_time"]), parse_task_time(row["end_time"]))]
                if result["conflicts"]:
                    result["errors"] = [{"field": "times", "message": "Proposed times conflict with the tasks below. Saved times were not changed."}]
                    return result
                saved = transaction.update_task_times(task_id, start_time, end_time)
            result.update(success=True, record=saved)
        except RepositoryError as error:
            result["errors"] = [{"field": "storage", "message": str(error)}]
        return result
