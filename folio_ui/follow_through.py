from datetime import datetime
import re

import streamlit as st
from demos.src.coursework_service import RepositoryError


def validate_reminder(enabled, value):
    """Return a canonical local minute timestamp, or None for disabled settings."""
    if not enabled:
        return None
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', value.strip()):
        raise ValueError('Enter a local reminder time as YYYY-MM-DDTHH:MM.')
    try:
        return datetime.strptime(value.strip(), '%Y-%m-%dT%H:%M').isoformat(timespec='minutes')
    except ValueError:
        raise ValueError('Enter a valid local reminder date and time.') from None


def render_follow_through(repository, visible_task_ids, backend=None):
    st.subheader('Progress and reminders')
    try:
        state = repository.RestoreSavedApplicationState()
    except RepositoryError:
        st.error('Progress could not be loaded. Refresh before making changes.')
        return
    plans = {p['id']: p for p in state['plans'] if p['active']}
    tasks = [t for t in state['tasks'] if t['plan_id'] in plans]
    for plan_id, plan in plans.items():
        own = [t for t in tasks if t['plan_id'] == plan_id]
        done = sum(bool(t['completed']) for t in own)
        st.write(f"{plan['name']} (#{plan_id}): {done} of {len(own)} tasks complete")
        st.progress(done / len(own) if own else 0.0)
        if not own:
            st.caption('This plan has no tasks yet.')
    notice = st.session_state.pop('follow_through_notice', None)
    if notice:
        st.success(notice)
    if backend is None:
        st.info('Progress is read-only. Completion saving and reminder delivery are not connected yet.')
    st.caption('Reminders require Folio and its browser session to remain active. Reminder settings do not reschedule tasks or resolve conflicts.')
    visible = {t['id']: t for t in tasks if t['id'] in visible_task_ids}
    if not visible:
        st.caption('Choose a date with scheduled tasks to change completion or reminders.')
        return
    task_id = st.selectbox('Task for completion or reminder', list(visible),
        format_func=lambda i: f"{plans[visible[i]['plan_id']]['name']} · {visible[i]['name']} (#{i})",
        key='follow_through_task')
    task = visible[task_id]
    current = bool(task['completed'])
    st.caption('Completed' if current else 'Not complete')
    if st.button('Mark incomplete' if current else 'Mark complete', disabled=backend is None):
        try:
            changed = backend.set_completed(task['plan_id'], task_id, not current, expected_completed=current)
            if changed is False:
                st.rerun()
            saved = repository.get_plan(task['plan_id'])
            updated = next((t for t in saved['tasks'] if t['id'] == task_id), None) if saved else None
            if updated is None or bool(updated['completed']) == current:
                raise RepositoryError('Completion could not be confirmed.')
            whole = bool(saved['tasks']) and all(t['completed'] for t in saved['tasks'])
            st.session_state['follow_through_notice'] = ('Congratulations! All tasks in this plan are complete.'
                if not current and whole else 'Congratulations! Task marked complete.' if not current else 'Task marked incomplete.')
            st.rerun()
        except (RepositoryError, ValueError):
            st.error('Completion could not be confirmed. Refresh and review the saved status before trying again.')
    setting = {'enabled': False, 'remind_at': None, 'revision': None}
    if backend is not None:
        try:
            setting = backend.get_reminder(task_id)
        except (RepositoryError, ValueError):
            st.error('Reminder settings could not be loaded. No changes were saved.')
            return
    if setting.get('needs_review'):
        st.warning('The task time changed. Its previous reminder is paused. Check the time and enable it again to confirm.')
    prefix = f"reminder_{task_id}_{setting['revision']}"
    with st.form(prefix):
        enabled = st.checkbox('Enable reminder', value=setting['enabled'], disabled=backend is None)
        value = st.text_input('Reminder time (YYYY-MM-DDTHH:MM)', value=setting['remind_at'] or task['start_time'], disabled=backend is None)
        save = st.form_submit_button('Save reminder', disabled=backend is None)
    if save:
        try:
            when = validate_reminder(enabled, value)
            backend.save_reminder(task_id, enabled=enabled, remind_at=when, expected_revision=setting['revision'])
            confirmed = backend.get_reminder(task_id)
            if confirmed['enabled'] != enabled or confirmed['remind_at'] != when:
                raise RepositoryError('Reminder save could not be confirmed.')
            st.session_state['follow_through_notice'] = 'Reminder saved. Keep Folio and its browser session active.' if enabled else 'Reminder disabled.'
            st.rerun()
        except (RepositoryError, ValueError) as error:
            st.error(str(error) if isinstance(error, ValueError) else 'Reminder save could not be confirmed. Refresh and review the saved settings before trying again.')


@st.fragment(run_every="2s")
def render_due_reminders(backend):
    alerts = st.session_state.setdefault("due_reminders", [])
    try:
        due = backend.claim_due()
        alerts.extend(due)
        if due:
            st.toast(f"Task reminder: {due[0]['name']}" if len(due) == 1 else f"{len(due)} task reminders are due.", duration="long")
    except RepositoryError:
        st.warning("Reminders could not be checked. Folio will retry.")
    for reminder in alerts:
        label = "Overdue reminder" if reminder["overdue"] else "Reminder"
        st.info(f"{label}: {reminder['name']} · {reminder['plan_name']} (task #{reminder['task_id']}, {reminder['remind_at'].replace('T', ' ')})")
    if alerts and st.button("Dismiss reminders"):
        st.session_state.pop("due_reminders", None)
        st.rerun(scope="app")
