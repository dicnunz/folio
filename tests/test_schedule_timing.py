"""C13 submission-to-render instrumentation for task creation and deletion."""
from datetime import date
from pathlib import Path
from time import perf_counter

from streamlit.testing.v1 import AppTest

from folio.application import open_application
from folio.planning import PlanningService


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_three_task_create_delete_visible_updates(tmp_path, monkeypatch):
    path = tmp_path / 'timing.sqlite3'
    monkeypatch.setenv('FOLIO_DATABASE', str(path))
    repo, service = open_application(path)
    cid = service.create_coursework({'course': 'TIMING', 'item_name': 'Essay', 'due_date': '2026-10-20'})['record']['id']
    saved = PlanningService(repo).save_plan(PlanningService(repo).new_plan(cid, 'assignment'))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run()
    app.session_state['schedule_date'] = date(2026, 10, 19)

    def open_plan():
        app.radio(key='folio_screen').set_value('Plan').run()
        app.selectbox[1].set_value(saved['plan']['id']).run()
        button(app, 'Open saved plan').click().run()

    for run in range(1, 4):
        open_plan()
        button(app, 'Add Task').click().run()
        for widget, value in zip(app.text_input[-3:], [f'Timed task {run}', '2026-10-19T17:00', '2026-10-19T18:00']):
            widget.set_value(value)
        start = perf_counter()
        button(app, 'Save plan').click().run()
        app.radio(key='folio_screen').set_value('Schedule').run()
        assert len(app.table[0].value) == 4 and not app.exception
        created = perf_counter() - start
        assert created < 2
        open_plan()
        app.checkbox[-1].check().run()
        button(app, 'Remove Tasks').click().run()
        start = perf_counter()
        button(app, 'Save plan').click().run()
        app.radio(key='folio_screen').set_value('Schedule').run()
        assert len(app.table[0].value) == 3 and not app.exception
        deleted = perf_counter() - start
        assert deleted < 2
        print(f'C13 AppTest run {run}: create_save_to_schedule={created:.6f}s delete_save_to_schedule={deleted:.6f}s')
