from streamlit.testing.v1 import AppTest

SCRIPT = '''
from folio_ui.sharing import render_sharing
class Repository:
    def restore_saved_application_state(self):
        return {'plans': [{'id': 1, 'name': 'Essay'}], 'coursework': [{'id': 4, 'course': 'CSE', 'item_name': 'Essay', 'due_date': '2026-10-25', 'score': 'PRIVATE_SENTINEL'}]}
    def get_plan(self, plan_id):
        return {'plan': {'id': 1, 'coursework_id': 4, 'name': 'Essay'}, 'tasks': [{'id': 8, 'name': 'Draft', 'start_time': '2026-10-22T10:00', 'end_time': '2026-10-22T11:00', 'completed': 'PRIVATE_SENTINEL'}]}
render_sharing(Repository())
'''

def button(app, label):
    return next(element for element in app.button if element.label == label)

def test_selection_invalidates_exports_and_mail():
    app = AppTest.from_string(SCRIPT).run()
    button(app, 'Prepare PDF and DOCX').click().run()
    assert app.session_state['share_pdf'].startswith(b'%PDF')
    button(app, 'Prepare instructor email').click().run()
    button(app, 'Create unsent email file').click().run()
    assert app.session_state['share_email']
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    for key in ('share_pdf', 'share_docx', 'share_email', 'share_body'):
        assert key not in app.session_state
    assert all('PRIVATE_SENTINEL' not in element.value for element in app.text)

def test_cancel_and_prepare_again_and_edit():
    app = AppTest.from_string(SCRIPT).run()
    button(app, 'Prepare instructor email').click().run()
    app.text_area[0].set_value('My edited message').run()
    button(app, 'Create unsent email file').click().run()
    assert b'My edited message' in app.session_state['share_email']
    app.text_area[0].set_value('Changed body').run()
    assert 'share_email' not in app.session_state
    button(app, 'Cancel prepared email').click().run()
    assert not app.text_area
    button(app, 'Prepare instructor email').click().run()
    assert 'Plan: Essay' in app.text_area[0].value
    assert not app.exception

def test_task_deselection_invalidates_mail():
    app = AppTest.from_string(SCRIPT).run()
    button(app, 'Prepare instructor email').click().run()
    button(app, 'Create unsent email file').click().run()
    app.multiselect[1].set_value([]).run()
    assert 'share_email' not in app.session_state
    assert 'Draft' not in app.text[0].value
