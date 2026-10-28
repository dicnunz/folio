"""Reviewable exports and unsent instructor email from persisted plans."""
import hashlib
import json
import streamlit as st
from folio.sharing import (ACADEMIC_FIELDS, LABELS, get_shareable_academic_data,
                           preview_text, export_pdf, export_docx, prepare_instructor_email)


def clear_prepared_share():
    for key in ('share_pdf', 'share_docx', 'share_email', 'share_recipient', 'share_subject', 'share_body', 'share_mail_open'):
        st.session_state.pop(key, None)


def render_sharing(repository):
    st.header('Share an academic plan')
    plans = repository.restore_saved_application_state()['plans']
    if not plans:
        clear_prepared_share()
        st.info('Save an academic plan before preparing a share.')
        return
    plan_names = {row['id']: row['name'] for row in plans}
    plan_id = st.selectbox('Saved plan', list(plan_names), format_func=lambda value: f'{plan_names[value]} (#{value})', key='share_plan')
    fields = st.multiselect('Academic fields', ACADEMIC_FIELDS, default=list(ACADEMIC_FIELDS), format_func=lambda value: LABELS[value], key='share_fields')
    tasks = repository.get_plan(plan_id)['tasks']
    indices = st.multiselect('Tasks to include', list(range(len(tasks))), default=list(range(len(tasks))), format_func=lambda value: f'{tasks[value]["name"]} (#{tasks[value]["id"]})', key=f'share_tasks_{plan_id}') if 'tasks' in fields else []
    data = get_shareable_academic_data(repository, plan_id, fields, indices)
    fingerprint = hashlib.sha256(json.dumps([plan_id, fields, indices, data], sort_keys=True).encode()).hexdigest()
    if st.session_state.get('share_fingerprint') != fingerprint:
        clear_prepared_share()
        st.session_state['share_fingerprint'] = fingerprint
    st.caption('Only the selected academic information below is included. Completion, scores, progress and rewards are excluded.')
    st.text(preview_text(data) or 'No academic content selected.')
    if not data or data == {'tasks': []}:
        return
    if st.button('Prepare PDF and DOCX'):
        try:
            st.session_state['share_pdf'] = export_pdf(data)
            st.session_state['share_docx'] = export_docx(data)
        except ValueError as error:
            st.error(str(error))
    if 'share_pdf' in st.session_state:
        st.download_button('Download PDF', st.session_state['share_pdf'], 'academic-plan.pdf', 'application/pdf')
        st.download_button('Download DOCX', st.session_state['share_docx'], 'academic-plan.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    if st.button('Prepare instructor email'):
        st.session_state['share_mail_open'] = True
        st.session_state['share_body'] = preview_text(data)
        st.session_state.pop('share_email', None)
    if st.session_state.get('share_mail_open'):
        st.caption('This creates an unsent email file with the current PDF and DOCX attached. Review the recipient, subject and body before using your mail app.')
        def invalidate_email():
            st.session_state.pop('share_email', None)
        recipient = st.text_input('Instructor email (optional)', key='share_recipient', on_change=invalidate_email)
        subject = st.text_input('Subject', value='Academic plan for review', key='share_subject', on_change=invalidate_email)
        body = st.text_area('Email body', key='share_body', height=220, on_change=invalidate_email)
        if st.button('Create unsent email file'):
            try:
                st.session_state['share_email'] = prepare_instructor_email(data, recipient, subject, body)
            except ValueError as error:
                st.error(str(error))
        if 'share_email' in st.session_state:
            st.download_button('Download unsent email', st.session_state['share_email'], 'academic-plan.eml', 'message/rfc822')
        st.button('Cancel prepared email', on_click=clear_prepared_share)
