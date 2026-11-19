"""Additional acceptance assertions, kept separate from the established suite.
Run: python -m pytest tests/results/m3/test_m3_regressions.py -v
The deadline test is intentionally a normal failing assertion until implemented.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import pytest
from folio.application import open_application
from folio.schedule_service import ScheduleService
from scripts.seed_schedule_fixture import seed

@pytest.fixture
def saved(tmp_path):
    path = tmp_path / 'm3.sqlite3'
    seed(path)
    repo, _ = open_application(path)
    return path, repo, ScheduleService(repo)

def test_deadline_late_preparation_is_rejected_without_mutation(saved):
    _, repo, service = saved
    before = repo.RestoreSavedApplicationState()
    outcome = service.reschedule_task(1, '2026-11-02T09:00', '2026-11-02T10:00')
    assert not outcome['success'], 'Task after coursework deadline 2026-10-30 was accepted'
    assert outcome['errors'], 'Deadline rejection needs meaningful feedback'
    assert repo.RestoreSavedApplicationState() == before

def test_valid_pre_deadline_correction_preserves_other_records(saved):
    _, repo, service = saved
    before = repo.RestoreSavedApplicationState()
    assert service.reschedule_task(1, '2026-10-29T09:00', '2026-10-29T10:00')['success']
    after = repo.RestoreSavedApplicationState()
    for key in ['plans', 'coursework', 'feedback']:
        assert before[key] == after[key]
    assert [t for t in before['tasks'] if t['id'] != 1] == [t for t in after['tasks'] if t['id'] != 1]

def test_completion_flags_repeat_undo_and_reopen_repository_only(saved):
    path, repo, _ = saved
    other = repo.get_plan(2)
    for completed in [True, True, False, True, False]:
        plan = repo.get_plan(1)
        plan['tasks'][0]['completed'] = completed
        repo.StorePlanData(**plan)
        repo, _ = open_application(path)
        assert bool(repo.get_plan(1)['tasks'][0]['completed']) == completed
        assert repo.get_plan(2) == other
        assert len(repo.RestoreSavedApplicationState()['tasks']) == 4
    # Does not claim UI completion, plan progress, notification or reward integration.
