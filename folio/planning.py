"""Student-controlled plan drafts using the shared academic repository."""
from copy import deepcopy
from datetime import datetime, time, timedelta

TEMPLATES = {
    'assignment': ('Understand requirements', 'Prepare a draft', 'Review and submit'),
    'test': ('Identify topics', 'Practice questions', 'Review difficult topics'),
    'other': ('Prepare', 'Work on coursework', 'Review work'),
}


class PlanningService:
    def __init__(self, repository):
        self.repository = repository

    def new_plan(self, coursework_id, template_id):
        records = self.repository.RestoreSavedApplicationState()['coursework']
        item = next((item for item in records if item['id'] == coursework_id), None)
        if item is None:
            raise ValueError('Choose saved coursework.')
        if template_id not in TEMPLATES:
            raise ValueError('Choose an available planning template.')
        due = datetime.fromisoformat(item['due_date'])
        start = datetime.combine(due.date() - timedelta(days=1), time(9))
        tasks = []
        for offset, name in enumerate(TEMPLATES[template_id]):
            task_start = start + timedelta(hours=offset)
            tasks.append({'name': name, 'start_time': task_start.isoformat(timespec='minutes'),
                          'end_time': (task_start + timedelta(hours=1)).isoformat(timespec='minutes'), 'completed': False})
        return {'plan': {'coursework_id': coursework_id, 'name': item['item_name'],
                         'template_id': template_id, 'notes': '', 'active': True},
                'tasks': tasks, 'feedback': []}

    def open_plan(self, plan_id):
        saved = self.repository.get_plan(plan_id)
        if saved is None:
            raise ValueError('The saved plan is no longer available.')
        return deepcopy(saved)

    def review_suggestion(self, draft, suggestion, decision, adapted_text=None, task_index=0):
        revised = deepcopy(draft)
        if decision not in ('accept', 'reject', 'adapt'):
            raise ValueError('Choose accept, reject or adapt.')
        if not suggestion.strip():
            raise ValueError('Enter the instructor suggestion to review.')
        if decision == 'reject':
            return revised
        applied = adapted_text if decision == 'adapt' else suggestion
        if not applied or not applied.strip():
            raise ValueError('Enter the adapted suggestion.')
        revised['feedback'].append({'suggestion': suggestion.strip(), 'decision': decision,
                                    'adapted_text': applied.strip() if decision == 'adapt' else None})
        if not isinstance(task_index, int) or not 0 <= task_index < len(revised['tasks']):
            raise ValueError('Choose a task to revise.')
        revised['tasks'][task_index]['name'] = applied.strip()
        return revised

    def save_plan(self, draft):
        revised = deepcopy(draft)
        if not revised['plan']['name'].strip():
            raise ValueError('Enter a plan name.')
        if not revised['tasks']:
            raise ValueError('Add at least one task.')
        original = self.open_plan(revised['plan']['id']) if revised['plan'].get('id') else None
        previous = {task['id']: task for task in original['tasks']} if original else {}
        for task in revised['tasks']:
            if not task['name'].strip():
                raise ValueError('Every task needs a name.')
            try:
                start = datetime.strptime(task['start_time'], '%Y-%m-%dT%H:%M')
                end = datetime.strptime(task['end_time'], '%Y-%m-%dT%H:%M')
                if start >= end:
                    raise ValueError()
            except (ValueError, TypeError):
                raise ValueError('Every task needs valid start and end dates and times, with end after start.') from None
            task['name'] = task['name'].strip()
            task['start_time'] = start.isoformat(timespec='minutes')
            task['end_time'] = end.isoformat(timespec='minutes')
            if task.get('id') in previous:
                task['completed'] = previous[task['id']]['completed']
            else:
                task['completed'] = False
        return self.repository.StorePlanData(revised['plan'], revised['tasks'], revised['feedback'])
