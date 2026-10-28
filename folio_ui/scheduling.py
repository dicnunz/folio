"""Dated daily/weekly schedule, exact conflicts and student corrections."""
from datetime import date, timedelta

import streamlit as st

from demos.src.coursework_service import RepositoryError
from folio.scheduling import ScheduleService, describe_task, tasks_in_period


def render_schedule(repository):
    st.title('Schedule')
    notice = st.session_state.pop('schedule_notice', None)
    if notice:
        st.success(notice)
    service = ScheduleService(repository)
    view = st.radio('Schedule view', ['Daily', 'Weekly'], horizontal=True)
    selected_date = st.date_input('Schedule date', value=date.today(), key='schedule_date')
    first = selected_date - timedelta(days=selected_date.weekday()) if view == 'Weekly' else selected_date
    last = first + timedelta(days=6 if view == 'Weekly' else 0)
    st.caption(f'{first.isoformat()} to {last.isoformat()} · Local times · Active saved plans')
    try:
        all_tasks = service.tasks()
        tasks = tasks_in_period(all_tasks, selected_date, weekly=view == 'Weekly')
    except (ValueError, RepositoryError) as error:
        st.error(str(error))
        return
    if not tasks:
        st.info('No scheduled tasks in this period. Save a plan or choose another date.')
        return
    st.table([{'Task ID': task['id'], 'Course': task['course'], 'Plan': task['plan_name'],
               'Task': task['name'], 'Start': task['start_time'], 'End': task['end_time'],
               'Conflict': ', '.join(f"Task #{other}" for other in task['conflict_ids']) or 'None'}
              for task in tasks])
    indexed = {task['id']: task for task in tasks}
    all_indexed = {task['id']: task for task in all_tasks}
    pairs = set()
    for task in tasks:
        for other_id in task['conflict_ids']:
            pair = tuple(sorted((task['id'], other_id)))
            if pair not in pairs:
                pairs.add(pair)
                st.warning(f"Conflict: {describe_task(task)} overlaps {describe_task(all_indexed[other_id])}.")
    if not pairs:
        st.success('No time conflicts in this period.')
    st.subheader('Correct a task time')
    st.caption('Choose the time yourself. A correction that still overlaps an active task is rejected; the saved time stays unchanged.')
    task_id = st.selectbox('Task to correct', list(indexed), format_func=lambda value: describe_task(indexed[value]))
    task = indexed[task_id]
    prefix = f"correct_{task_id}_{task['start_time']}_{task['end_time']}"
    with st.form(prefix):
        start = st.text_input('Corrected start (YYYY-MM-DDTHH:MM)', value=task['start_time'])
        end = st.text_input('Corrected end (YYYY-MM-DDTHH:MM)', value=task['end_time'])
        save = st.form_submit_button('Save corrected time')
    if save:
        try:
            service.correct_time(task_id, start, end)
            st.session_state['schedule_notice'] = f'Time corrected for task #{task_id}.'
            st.rerun()
        except (ValueError, RepositoryError) as error:
            st.error(str(error))
