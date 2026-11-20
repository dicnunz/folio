"""Combined saved-plan schedules and explicit student time corrections."""
from datetime import datetime, time, timedelta

from demos.src.scheduling import combine_active_plan_tasks
from folio.deadlines import preparation_notice
from folio.schedule_service import ScheduleService as StoredSchedule


class ScheduleService:
    def __init__(self, repository):
        self.repository = repository

    def tasks(self, selected_date=None, weekly=False):
        state = self.repository.RestoreSavedApplicationState()
        tasks = combine_active_plan_tasks(state)
        if any(task.get('preparation') for task in tasks):
            contexts = self.repository.preparation_contexts()
            linked = {plan['id']: plan['coursework_id'] for plan in state['plans']}
            for task in tasks:
                notice = preparation_notice(task, contexts.get(linked[task['plan_id']]))
                if notice:
                    task['preparation_notice'] = notice
        return tasks_in_period(tasks, selected_date, weekly)

    def correct_time(self, task_id, start_text, end_text, expected_times=None):
        result = StoredSchedule(self.repository).reschedule_task(task_id, start_text, end_text, expected_times)
        if result['success']:
            return self.repository.get_plan(result['record']['plan_id'])
        messages = [error['message'] for error in result['errors'] if error['field'] != 'times']
        if result['conflicts']:
            details = '; '.join(describe_task({**task, 'plan_name': task['plan']}) for task in result['conflicts'])
            messages.append(f'Chosen time conflicts with {details}. Saved time unchanged.')
        raise ValueError(' '.join(messages))


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
