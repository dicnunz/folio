from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from folio.application import open_application
from scripts.seed_schedule_fixture import seed

APP = Path(__file__).resolve().parents[1] / 'app.py'


def button(app, label):
    return next(item for item in app.button if item.label == label)


def setup_app(tmp_path, monkeypatch):
    path = tmp_path / 'schedule.sqlite3'
    seed(path)
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    app = AppTest.from_file(str(APP), default_timeout=15).run()
    app.date_input(key='schedule_date').set_value(date(2026,10,26)).run()
    assert not app.exception
    return path, app


def test_daily_weekly_conflict_indicators_and_student_resolution(tmp_path, monkeypatch):
    path, app = setup_app(tmp_path, monkeypatch)
    assert len(app.dataframe[-1].value) == 4
    assert len(app.warning) == 2
    assert all('Overlap: 2026-10-26T' in warning.value for warning in app.warning)
    app.radio(key='schedule_view').set_value('Daily').run()
    rows = app.dataframe[-1].value
    assert set(rows['Task ID']) == {1,2,4}
    assert all('⚠' in indicator for indicator in rows['Conflicts'])
    next(item for item in app.selectbox if item.label=='Task to correct').select(2).run()
    next(item for item in app.text_input if item.label=='New start time').set_value('2026-10-26T10:15')
    next(item for item in app.text_input if item.label=='New end time').set_value('2026-10-26T11:45')
    button(app,'Save corrected times').click().run()
    assert app.error and any('Saved times were not changed' in item.value for item in app.error)
    repository, _ = open_application(path)
    assert repository.get_plan(1)['tasks'][1]['start_time']=='2026-10-26T10:30'
    next(item for item in app.text_input if item.label=='New start time').set_value('2026-10-26T12:00')
    next(item for item in app.text_input if item.label=='New end time').set_value('2026-10-26T13:00')
    button(app,'Save corrected times').click().run()
    assert not app.exception and not app.warning
    assert all(value=='None' for value in app.dataframe[-1].value['Conflicts'])
    assert any('Task #2 saved:' in item.value for item in app.success)
    restarted = AppTest.from_file(str(APP),default_timeout=15).run()
    restarted.date_input(key='schedule_date').set_value(date(2026,10,26)).run()
    row = restarted.dataframe[-1].value.set_index('Task ID').loc[2]
    assert row['Start']=='2026-10-26T12:00' and row['Plan ID']==1


def test_plan_changes_and_deletions_refresh_visible_schedule(tmp_path, monkeypatch):
    path, app = setup_app(tmp_path,monkeypatch)
    repository, _ = open_application(path)
    aggregate = repository.get_plan(1)
    aggregate['plan']['name'] = 'New plan name'
    aggregate['tasks'] = [row for row in aggregate['tasks'] if row['id'] != 2]
    repository.StorePlanData(**aggregate)
    button(app,'Refresh schedule').click().run()
    assert set(app.dataframe[-1].value['Task ID']) == {1,3,4}
    assert 'New plan name' in set(app.dataframe[-1].value['Plan'])
    assert not app.warning
    repository.delete_plan(1)
    button(app,'Refresh schedule').click().run()
    assert list(app.dataframe[-1].value['Task ID']) == [4]
    assert not app.exception


def test_empty_period_and_inactive_plan(tmp_path, monkeypatch):
    path, app = setup_app(tmp_path,monkeypatch)
    app.date_input(key='schedule_date').set_value(date(2030,1,1)).run()
    assert any('No tasks from active plans' in item.value for item in app.info)
    assert not app.warning
    repository, _ = open_application(path)
    for plan in repository.restore_saved_application_state()['plans']:
        repository.StorePlanData({**plan,'active':False})
    app.date_input(key='schedule_date').set_value(date(2026,10,26)).run()
    assert len(app.dataframe[-1].value)==0
    assert not app.exception
