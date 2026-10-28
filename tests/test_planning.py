from copy import deepcopy

import pytest
from folio.application import open_application
from folio.planning import PlanningService


@pytest.fixture
def setup(tmp_path):
    repo, coursework = open_application(tmp_path / 'academic.db')
    item = coursework.create_coursework({'course': 'CS', 'item_name': 'Essay', 'due_date': '2026-11-01', 'score': ''})
    record = repo.restore_saved_application_state()['coursework'][0]
    return repo, PlanningService(repo), record['id']


def test_template_edit_save_reopen_preserves_ids_and_completion(setup):
    repo, service, cid = setup
    draft = service.new_plan(cid, 'assignment')
    draft['tasks'][0].update(name='Read chapter', start_time='2026-10-23T10:00', end_time='2026-10-23T11:00')
    saved = service.save_plan(draft)
    saved['tasks'][0]['completed'] = True
    repo.StorePlanData(saved['plan'], saved['tasks'], saved['feedback'])
    revision = service.open_plan(saved['plan']['id'])
    revision['tasks'][0]['name'] = 'Read revised chapter'
    revised = service.save_plan(revision)
    assert revised['tasks'][0]['id'] == saved['tasks'][0]['id']
    assert revised['tasks'][0]['completed'] == 1
    assert service.open_plan(saved['plan']['id']) == revised


def test_feedback_is_explicit_and_decline_or_reject_changes_nothing(setup):
    repo, service, cid = setup
    saved = service.save_plan(service.new_plan(cid, 'test'))
    before = deepcopy(repo.restore_saved_application_state())
    rejected = service.review_suggestion(saved, 'Review examples', 'reject')
    assert rejected == saved
    accepted = service.review_suggestion(saved, 'Review examples', 'accept')
    assert accepted['tasks'][0]['name'] == 'Review examples'
    assert repo.restore_saved_application_state() == before  # declining this draft needs no write
    adapted = service.review_suggestion(saved, 'Review examples', 'adapt', 'Review two examples')
    assert service.save_plan(adapted)['tasks'][0]['name'] == 'Review two examples'


def test_validation_does_not_write(setup):
    repo, service, cid = setup
    before = repo.restore_saved_application_state()
    draft = service.new_plan(cid, 'other')
    draft['tasks'][0]['end_time'] = draft['tasks'][0]['start_time']
    with pytest.raises(ValueError):
        service.save_plan(draft)
    assert repo.restore_saved_application_state() == before
    with pytest.raises(ValueError):
        service.new_plan(999, 'other')


def test_three_templates_and_revising_only_selected_plan(setup):
    repo, service, cid = setup
    plans = []
    for template in ('assignment', 'test', 'other'):
        item = repo.store_coursework('CREATE', {'course': 'CS', 'item_name': template.title(), 'due_date': '2026-11-01', 'score': None})
        draft = service.new_plan(item['id'], template)
        draft['tasks'][0]['name'] = f'My {template} task'
        plans.append(service.save_plan(draft))
    original_others = [service.open_plan(plan['plan']['id']) for plan in plans[1:]]
    revised = service.open_plan(plans[0]['plan']['id'])
    removed_id = revised['tasks'].pop()['id']
    revised['tasks'].append({'name': 'Additional review', 'start_time': '2026-10-30T15:00', 'end_time': '2026-10-30T16:00'})
    revised['tasks'][0]['name'] = 'Latest task'
    saved = service.save_plan(revised)
    assert all(task['id'] != removed_id for task in saved['tasks'])
    assert saved['tasks'][0]['name'] == 'Latest task'
    assert [service.open_plan(plan['plan']['id']) for plan in plans[1:]] == original_others


def test_feedback_exact_original_and_adapted_values(setup):
    repo, service, cid = setup
    saved = service.save_plan(service.new_plan(cid, 'assignment'))
    accepted = service.save_plan(service.review_suggestion(saved, 'Review chapter 2', 'accept'))
    assert accepted['tasks'][0]['name'] == 'Review chapter 2'
    assert accepted['feedback'][0]['decision'] == 'accept'
    other = service.save_plan(service.new_plan(cid, 'other'))
    adapted = service.save_plan(service.review_suggestion(other, 'Review chapter 2', 'adapt', 'Review chapter 3'))
    assert adapted['tasks'][0]['name'] == 'Review chapter 3'
    assert adapted['feedback'][0]['adapted_text'] == 'Review chapter 3'
