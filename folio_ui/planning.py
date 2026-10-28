"""Plan screen. Edits remain in a session draft until the student saves."""
from copy import deepcopy

import streamlit as st

from demos.src.coursework_service import RepositoryError
from folio.planning import PlanningService, TEMPLATES
from folio.scheduling import ScheduleService, plan_conflict_messages


def render_planning(repository):
    st.title('Plan')
    service = PlanningService(repository)
    try:
        state = repository.RestoreSavedApplicationState()
    except RepositoryError as error:
        st.error(str(error))
        return
    coursework = {item['id']: item for item in state['coursework']}
    if not coursework:
        st.info('Save coursework on the Coursework screen before making a plan.')
        return
    notice = st.session_state.pop('plan_notice', None)
    if notice:
        st.success(notice)
    for message in st.session_state.pop('plan_conflict_notices', []):
        st.warning(message)
    ids = list(coursework)
    preferred = st.session_state.get('planning_coursework_id')
    cid = st.selectbox('Coursework', ids, index=ids.index(preferred) if preferred in ids else 0,
                       format_func=lambda value: f"{coursework[value]['course']} · {coursework[value]['item_name']} (#{value})")
    available = {plan['id']: plan for plan in state['plans'] if plan['coursework_id'] == cid}
    plan_id = st.selectbox('Saved plan', [None, *available],
                           format_func=lambda value: 'New plan' if value is None else f"{available[value]['name']} (#{value})")
    template = st.selectbox('Planning template', list(TEMPLATES), format_func=str.title)
    if st.button('Start plan' if plan_id is None else 'Open saved plan'):
        try:
            st.session_state['plan_draft'] = service.new_plan(cid, template) if plan_id is None else service.open_plan(plan_id)
            st.session_state['plan_revision'] = st.session_state.get('plan_revision', 0) + 1
            st.session_state.pop('plan_before_feedback', None)
        except (ValueError, RepositoryError) as error:
            st.error(str(error))
    draft = st.session_state.get('plan_draft')
    if draft is None or draft['plan']['coursework_id'] != cid:
        return
    revision = st.session_state.get('plan_revision', 0)
    st.caption('Suggested times are editable. Review each task before saving. Changes stay in this draft until Save plan.')
    editor = st.empty()
    with editor.container():
        prefix = f'plan_{revision}'
        with st.container():
            name = st.text_input('Plan name', draft['plan']['name'], key=f'{prefix}_name')
            notes = st.text_area('Plan notes', draft['plan'].get('notes', ''), key=f'{prefix}_notes')
            edited = []
            selected_indices = []
            for index, task in enumerate(draft['tasks']):
                st.subheader(f'Task {index + 1}')
                item = deepcopy(task)
                item['name'] = st.text_input('Task name', task['name'], key=f'{prefix}_{index}_name')
                item['start_time'] = st.text_input('Start (YYYY-MM-DDTHH:MM)', task['start_time'], key=f'{prefix}_{index}_start')
                item['end_time'] = st.text_input('End (YYYY-MM-DDTHH:MM)', task['end_time'], key=f'{prefix}_{index}_end')
                remove = st.checkbox('Remove task', key=f'{prefix}_{index}_remove')
                edited.append(item)
                if remove:
                    selected_indices.append(index)
            def change_tasks(action):
                updated = deepcopy(draft)
                updated['plan'].update(name=st.session_state[f'{prefix}_name'],
                                       notes=st.session_state[f'{prefix}_notes'])
                updated['tasks'] = []
                for index, task in enumerate(draft['tasks']):
                    if action == 'remove' and st.session_state[f'{prefix}_{index}_remove']:
                        continue
                    item = deepcopy(task)
                    for field, suffix in (('name', 'name'), ('start_time', 'start'), ('end_time', 'end')):
                        item[field] = st.session_state[f'{prefix}_{index}_{suffix}']
                    updated['tasks'].append(item)
                if action == 'add':
                    updated['tasks'].append({'name': '', 'start_time': '', 'end_time': '', 'completed': False})
                st.session_state['plan_draft'] = updated
                st.session_state['plan_revision'] = revision + 1

            add_column, remove_column = st.columns(2)
            add_column.button('Add Task', on_click=change_tasks, args=('add',))
            remove_column.button('Remove Tasks', disabled=not selected_indices,
                                 type='primary' if selected_indices else 'secondary',
                                 on_click=change_tasks, args=('remove',))
            save = st.button('Save plan')
            st.subheader('Instructor feedback (optional)')
            st.caption('Paste feedback you received. Accept or adapt changes the selected task name in the draft. Review its times above, then save. Reject leaves the plan unchanged.')
            target = st.selectbox('Task to revise', list(range(len(draft['tasks']))), format_func=lambda value: draft['tasks'][value]['name'] or f'Task {value + 1}')
            suggestion = st.text_area('Instructor suggestion')
            decision = st.radio('Decision', ['accept', 'reject', 'adapt'], format_func=str.title, horizontal=True)
            adapted = st.text_area('Adapted suggestion')
            review = st.button('Review suggestion')
        if save or review:
            draft = deepcopy(draft)
            draft['plan'].update(name=name, notes=notes)
            draft['tasks'] = edited
            st.session_state['plan_draft'] = draft
            if save:
                try:
                    st.session_state['plan_draft'] = service.save_plan(draft)
                    st.session_state['plan_notice'] = 'Plan saved.'
                    st.session_state.pop('plan_before_feedback', None)
                except (ValueError, RepositoryError) as error:
                    st.error(str(error))
                    return
                try:
                    st.session_state['plan_conflict_notices'] = plan_conflict_messages(
                        ScheduleService(repository).tasks(), st.session_state['plan_draft']['plan']['id'])
                except (ValueError, RepositoryError) as error:
                    st.session_state['plan_conflict_notices'] = [f'Plan saved. Review Schedule for conflicts: {error}']
            if save:
                st.session_state['plan_revision'] = revision + 1
                editor.empty()
                st.rerun()
        if review:
            try:
                target_index = target
                revised = service.review_suggestion(draft, suggestion, decision, adapted, target_index)
                if decision == 'reject':
                    st.info('Suggestion rejected. Saved plan unchanged.')
                else:
                    st.session_state.setdefault('plan_before_feedback', deepcopy(draft))
                    st.session_state['plan_draft'] = revised
                    st.session_state['plan_revision'] = revision + 1
                    editor.empty()
                    st.rerun()
            except ValueError as error:
                st.error(str(error))
        if 'plan_before_feedback' in st.session_state:
            st.info('Feedback is in the draft. Save plan above to apply the revision, or decline below.')
            if st.button('Decline feedback revision'):
                st.session_state['plan_draft'] = st.session_state.pop('plan_before_feedback')
                st.session_state['plan_revision'] = revision + 1
                st.session_state['plan_notice'] = 'Feedback revision declined. Saved plan unchanged.'
                editor.empty()
                st.rerun()
