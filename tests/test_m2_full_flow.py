"""CSE-23 M2 walkthrough through the actual app using disposable SQLite."""
from datetime import date
from email import policy
from email.parser import BytesParser
from pathlib import Path

from streamlit.testing.v1 import AppTest

from folio.application import open_application


APP = Path(__file__).resolve().parents[1] / 'app.py'


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_entry_plan_restart_schedule_correction_export_and_revision(tmp_path, monkeypatch):
    path = tmp_path / 'walkthrough.sqlite3'
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    repo, _ = open_application(path)
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    plan_ids = []
    for course, name in [('CS', 'Essay'), ('MATH', 'Exam')]:
        app = AppTest.from_file(str(APP), default_timeout=15).run()
        for widget, value in zip(app.text_input, [course, name, '2026-10-20', '', '', '']):
            widget.set_value(value)
        click(app, 'Save coursework')
        coursework_id = repo.RestoreSavedApplicationState()['coursework'][-1]['id']
        app.selectbox(key='coursework_picker').set_value(coursework_id).run()
        click(app, 'Use for planning')
        app.radio(key='folio_screen').set_value('Plan').run()
        app.selectbox[0].set_value(coursework_id).run()
        click(app, 'Start plan')
        click(app, 'Save plan')
        plan_ids.append(repo.RestoreSavedApplicationState()['plans'][-1]['id'])
        if course == 'MATH':
            assert len(app.warning) == 3
            assert all('Open Schedule' in warning.value for warning in app.warning)
    # New application session restores both saved plans and their task IDs.
    before = repo.RestoreSavedApplicationState()
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    assert repo.RestoreSavedApplicationState() == before
    app.radio(key='folio_screen').set_value('Schedule').run()
    app.date_input[0].set_value(date(2026, 10, 19)).run()
    assert len(app.table[0].value) == 6
    assert len(app.warning) == 3
    assert all('CS / Essay' in warning.value and 'MATH / Exam' in warning.value for warning in app.warning)
    next(r for r in app.radio if r.label == 'Schedule view').set_value('Weekly').run()
    assert len(app.table[0].value) == 6
    target_id = before['tasks'][0]['id']
    app.selectbox[0].set_value(target_id).run()
    app.text_input[0].set_value('2026-10-19T10:30')
    app.text_input[1].set_value('2026-10-19T11:30')
    click(app, 'Save corrected time')
    assert 'Saved time unchanged' in app.error[0].value
    assert repo.RestoreSavedApplicationState() == before
    app.text_input[0].set_value('2026-10-19T18:00')
    app.text_input[1].set_value('2026-10-19T19:00')
    click(app, 'Save corrected time')
    assert len(app.warning) == 2
    corrected = repo.get_plan(plan_ids[0])
    assert corrected['tasks'][0]['id'] == target_id
    assert corrected['tasks'][0]['start_time'] == '2026-10-19T18:00'
    app.radio(key='folio_screen').set_value('Share').run()
    app.selectbox[0].set_value(plan_ids[0]).run()
    assert '2026-10-19T18:00' in app.text[0].value
    click(app, 'Prepare PDF and DOCX')
    assert app.session_state['share_pdf'].startswith(b'%PDF')
    assert app.session_state['share_docx'].startswith(b'PK')
    click(app, 'Prepare instructor email')
    app.text_input[0].set_value('advisor@example.test').run()
    click(app, 'Create unsent email file')
    mail = BytesParser(policy=policy.default).parsebytes(app.session_state['share_email'])
    assert len(list(mail.iter_attachments())) == 2
    assert '2026-10-19T18:00' in mail.get_body(preferencelist=('plain',)).get_content()
    app.radio(key='folio_screen').set_value('Plan').run()
    app.selectbox[0].set_value(corrected['plan']['coursework_id']).run()
    app.selectbox[1].set_value(plan_ids[0]).run()
    click(app, 'Open saved plan')
    next(area for area in app.text_area if area.label == 'Instructor suggestion').set_value('Review chapter 2')
    click(app, 'Review suggestion')
    assert repo.get_plan(plan_ids[0]) == corrected
    click(app, 'Decline feedback revision')
    assert repo.get_plan(plan_ids[0]) == corrected
    next(area for area in app.text_area if area.label == 'Instructor suggestion').set_value('Review chapter 2')
    click(app, 'Review suggestion')
    click(app, 'Save plan')
    assert repo.get_plan(plan_ids[0])['tasks'][0]['name'] == 'Review chapter 2'
    app.checkbox[-1].check().run()
    click(app, 'Remove Tasks')
    click(app, 'Save plan')
    app.radio(key='folio_screen').set_value('Schedule').run()
    app.date_input[0].set_value(date(2026, 10, 19)).run()
    assert len(app.table[0].value) == 5
    assert any(row['Task'] == 'Review chapter 2' for _, row in app.table[0].value.iterrows())
    assert repo.get_plan(plan_ids[1]) == {'plan': before['plans'][1], 'tasks': before['tasks'][3:], 'feedback': []}
