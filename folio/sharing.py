"""Student-selected academic sharing. All serializers enforce the same allowlist."""
from io import BytesIO
from pathlib import Path
from email.message import EmailMessage
from email import policy

ACADEMIC_FIELDS = ('name', 'course', 'item_name', 'due_date', 'notes', 'tasks')
TASK_FIELDS = ('name', 'start_time', 'end_time')
LABELS = {'name': 'Plan', 'course': 'Course', 'item_name': 'Coursework', 'due_date': 'Due date', 'notes': 'Notes', 'tasks': 'Tasks'}


def filter_academic_data(data, selected_fields=ACADEMIC_FIELDS, selected_tasks=None):
    fields = set(selected_fields)
    result = {key: data[key] for key in ACADEMIC_FIELDS if key != 'tasks' and key in fields and key in data and isinstance(data[key], str)}
    if 'tasks' in fields and 'tasks' in data:
        chosen = None if selected_tasks is None else set(selected_tasks)
        result['tasks'] = [{key: task[key] for key in TASK_FIELDS if key in task and isinstance(task[key], str)}
                           for index, task in enumerate(data.get('tasks', [])) if isinstance(task, dict) and (chosen is None or index in chosen)]
    return result


def get_shareable_academic_data(repository, plan_id, selected_fields=ACADEMIC_FIELDS, selected_tasks=None):
    aggregate = repository.get_plan(plan_id)
    if aggregate is None:
        raise ValueError('Saved plan was not found.')
    coursework = next((row for row in repository.restore_saved_application_state()['coursework'] if row['id'] == aggregate['plan']['coursework_id']), {})
    data = {**coursework, **aggregate['plan'], 'tasks': aggregate['tasks']}
    return filter_academic_data(data, selected_fields, selected_tasks)


def preview_text(academic_data):
    data = filter_academic_data(academic_data)
    lines = []
    for field, value in data.items():
        if field == 'tasks':
            lines.append('Tasks:')
            for task in value:
                lines.append(' | '.join(task.get(key, '') for key in TASK_FIELDS))
        else:
            lines.append(f'{LABELS[field]}: {value}')
    return '\n'.join(lines)


def export_pdf(academic_data):
    from fpdf import FPDF
    pdf = FPDF()
    fonts = [Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf'), Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
    font = next((path for path in fonts if path.exists()), None)
    if font is None:
        raise ValueError('Install a Unicode TrueType font to export PDF.')
    pdf.add_font('Academic', fname=str(font))
    pdf.add_page()
    pdf.set_font('Academic', size=11)
    pdf.set_title('Academic plan')
    for line in preview_text(academic_data).splitlines():
        pdf.multi_cell(0, 7, text=line, new_x='LMARGIN', new_y='NEXT')
    return bytes(pdf.output())


def export_docx(academic_data):
    from docx import Document
    document = Document()
    document.core_properties.title = 'Academic plan'
    document.core_properties.author = ''
    document.core_properties.last_modified_by = ''
    document.core_properties.comments = ''
    for line in preview_text(academic_data).splitlines():
        document.add_paragraph(line)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def prepare_instructor_email(academic_data, recipient='', subject='Academic plan for review', body=None):
    for value in (recipient, subject):
        if '\r' in value or '\n' in value:
            raise ValueError('Email headers must contain a single line.')
    data = filter_academic_data(academic_data)
    message = EmailMessage(policy=policy.SMTP)
    if recipient:
        message['To'] = recipient
    message['Subject'] = subject
    message.set_content(preview_text(data) if body is None else body)
    message.add_attachment(export_pdf(data), maintype='application', subtype='pdf', filename='academic-plan.pdf')
    message.add_attachment(export_docx(data), maintype='application', subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', filename='academic-plan.docx')
    return message.as_bytes()
