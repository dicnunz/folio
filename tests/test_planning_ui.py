from streamlit.testing.v1 import AppTest
from folio.application import open_application


def build_app(tmp_path):
    path = tmp_path / 'ui.db'
    repo, service = open_application(path)
    service.create_coursework({'course': 'CS', 'item_name': 'Essay', 'due_date': '2026-11-01', 'score': ''})
    source = f"from folio.application import open_application\nfrom folio_ui.planning import render_planning\nrepo, _ = open_application({str(path)!r})\nrender_planning(repo)"
    return repo, AppTest.from_string(source).run()


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()


def test_save_edit_reopen_and_feedback_decline(tmp_path):
    repo, app = build_app(tmp_path)
    assert not app.exception
    click(app, 'Start plan')
    assert len(app.text_input) == 10
    click(app, 'Save plan')
    saved = repo.RestoreSavedApplicationState()
    assert len(saved['plans']) == 1
    before = repo.get_plan(saved['plans'][0]['id'])
    next(area for area in app.text_area if area.label == 'Instructor suggestion').input('Review chapter 2')
    click(app, 'Review suggestion')
    assert repo.get_plan(before['plan']['id']) == before
    click(app, 'Decline feedback revision')
    assert repo.get_plan(before['plan']['id']) == before
    app.selectbox[1].select(before['plan']['id']).run()
    click(app, 'Open saved plan')
    assert app.text_input[0].value == 'Essay'
    assert not app.exception


def test_remove_and_add_task(tmp_path):
    repo, app = build_app(tmp_path)
    click(app, 'Start plan')
    assert next(b for b in app.button if b.label == 'Remove Tasks').disabled
    app.checkbox[0].check().run()
    assert not next(b for b in app.button if b.label == 'Remove Tasks').disabled
    click(app, 'Remove Tasks')
    assert len(app.session_state['plan_draft']['tasks']) == 2
    assert next(b for b in app.button if b.label == 'Remove Tasks').disabled
    assert not any(box.value for box in app.checkbox)
    assert not repo.RestoreSavedApplicationState()['plans']
    repo, app = build_app(tmp_path / 'adding')
    click(app, 'Start plan')
    click(app, 'Add Task')
    assert len(app.session_state['plan_draft']['tasks']) == 4
    assert app.text_input[-3].value == ''
    assert not repo.RestoreSavedApplicationState()['plans']


def test_feedback_review_retains_unsaved_task_edits(tmp_path):
    repo, app = build_app(tmp_path)
    click(app, 'Start plan')
    app.text_input[4].input('MY SECOND TASK EDIT')
    next(area for area in app.text_area if area.label == 'Plan notes').input('My unsaved notes')
    next(area for area in app.text_area if area.label == 'Instructor suggestion').input('Review chapter 2')
    click(app, 'Review suggestion')
    draft = app.session_state['plan_draft']
    assert draft['tasks'][0]['name'] == 'Review chapter 2'
    assert draft['tasks'][1]['name'] == 'MY SECOND TASK EDIT'
    assert draft['plan']['notes'] == 'My unsaved notes'
    assert not repo.RestoreSavedApplicationState()['plans']
    click(app, 'Save plan')
    saved = repo.RestoreSavedApplicationState()
    assert saved['tasks'][1]['name'] == 'MY SECOND TASK EDIT'
    assert saved['plans'][0]['notes'] == 'My unsaved notes'


def test_multiple_removal_retains_edits_until_saved(tmp_path):
    repo, app = build_app(tmp_path)
    click(app, 'Start plan')
    click(app, 'Save plan')
    before = repo.RestoreSavedApplicationState()
    app.text_input[4].input('Keep edited task').run()
    app.checkbox[0].check().run()
    app.checkbox[2].check().run()
    click(app, 'Remove Tasks')
    assert [t['name'] for t in app.session_state['plan_draft']['tasks']] == ['Keep edited task']
    assert repo.RestoreSavedApplicationState() == before
    assert next(b for b in app.button if b.label == 'Remove Tasks').disabled
    click(app, 'Save plan')
    assert len(repo.RestoreSavedApplicationState()['tasks']) == 1
    assert not app.exception


def test_selection_alone_does_not_remove_on_save_or_add(tmp_path):
    repo, app = build_app(tmp_path)
    click(app, 'Start plan')
    app.checkbox[0].check().run()
    click(app, 'Save plan')
    assert len(repo.RestoreSavedApplicationState()['tasks']) == 3
    app.checkbox[0].check().run()
    click(app, 'Add Task')
    assert len(app.session_state['plan_draft']['tasks']) == 4


def test_remove_all_then_add_and_invalid_empty_save(tmp_path):
    repo, app = build_app(tmp_path)
    click(app, 'Start plan')
    for box in app.checkbox:
        box.check()
    app.run()
    click(app, 'Remove Tasks')
    assert not app.session_state['plan_draft']['tasks']
    assert next(b for b in app.button if b.label == 'Remove Tasks').disabled
    click(app, 'Save plan')
    assert any('at least one task' in error.value for error in app.error)
    assert not repo.RestoreSavedApplicationState()['plans']
    click(app, 'Add Task')
    assert len(app.session_state['plan_draft']['tasks']) == 1
    assert not app.exception
