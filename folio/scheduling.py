"""Combined saved-plan schedules and explicit student time corrections."""
from datetime import datetime, time, timedelta

from demos.src.scheduling import combine_active_plan_tasks
from folio.planning import PlanningService


class ScheduleService:
    def __init__(self, repository):
        self.repository = repository

    def tasks(self, selected_date=None, weekly=False):
        tasks = combine_active_plan_tasks(self.repository.RestoreSavedApplicationState())
        return tasks_in_period(tasks, selected_date, weekly)

    def correct_time(self, task_id, start_text, end_text):
        try:
            start, end = (datetime.strptime(value, '%Y-%m-%dT%H:%M') for value in (start_text, end_text))
            if start >= end:
                raise ValueError()
        except (TypeError, ValueError):
            raise ValueError('Use local YYYY-MM-DDTHH:MM times, with end after start.') from None
        tasks = self.tasks()
        target = next((task for task in tasks if task['id'] == task_id), None)
        if target is None:
            raise ValueError('The active task is no longer available. Refresh the schedule.')
        conflicts = [task for task in tasks if task['id'] != task_id and start < task['end'] and end > task['start']]
        if conflicts:
            detail = '; '.join(describe_task(task) for task in conflicts)
            raise ValueError(f'Chosen time conflicts with {detail}. Saved time unchanged.')
        planning = PlanningService(self.repository)
        draft = planning.open_plan(target['plan_id'])
        task = next(task for task in draft['tasks'] if task['id'] == task_id)
        task.update(start_time=start.isoformat(timespec='minutes'), end_time=end.isoformat(timespec='minutes'))
        return planning.save_plan(draft)


def describe_task(task):
    return (f"{task['course']} / {task['plan_name']} / {task['name']} (task #{task['id']}, "
            f"{task['start_time']} to {task['end_time']})")


def plan_conflict_messages(tasks, plan_id):
    indexed = {task['id']: task for task in tasks}
    pairs = set()
    for task in tasks:
        if task['plan_id'] == plan_id:
            pairs.update(tuple(sorted((task['id'], other))) for other in task['conflict_ids'])
    return [f"Conflict: {describe_task(indexed[first])} overlaps {describe_task(indexed[second])}. "
            'Open Schedule to choose corrected times.' for first, second in sorted(pairs)]


def tasks_in_period(tasks, selected_date=None, weekly=False):
    if selected_date is None:
        return tasks
    first_date = selected_date - timedelta(days=selected_date.weekday()) if weekly else selected_date
    start = datetime.combine(first_date, time.min)
    end = start + timedelta(days=7 if weekly else 1)
    return [task for task in tasks if task['start'] < end and task['end'] > start]
