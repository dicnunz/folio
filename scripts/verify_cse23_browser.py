"""Reproducible CSE-23 browser evidence using a disposable database.

python -m scripts.verify_cse23_browser
Planning input is an explicit fixture because the owning editor/export screens
are absent; coursework entry and schedule correction use the real browser UI.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import sqlite3
import subprocess
import sys
import tempfile
from time import perf_counter, sleep
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect
from folio.application import open_application
from folio.schedule_service import ScheduleService
from scripts.seed_schedule_fixture import add_sample_plans

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / 'cse-23'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='folio-cse23-') as directory:
        path = Path(directory) / 'schedule.sqlite3'
        repository, _ = open_application(path)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        url = f'http://127.0.0.1:{port}'
        env = {**os.environ, 'FOLIO_DATABASE': str(path), 'PYTHONDONTWRITEBYTECODE': '1'}
        process = None
        log = (OUT / 'server.log').open('w')
        result = {'recorded_at': datetime.now(ZoneInfo('America/New_York')).isoformat(),
                  'platform': platform.platform(), 'python': platform.python_version(),
                  'sqlite': sqlite3.sqlite_version, 'base_commit': subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                  'scope': 'real coursework controls and schedule UI; fixture-assisted plans, task deletion and plan deletion; export/revision screens unavailable',
                  'timing_method': 'perf_counter immediately before button click through rendered schedule/conflict assertions',
                  'correction_seconds': [], 'conflict_seconds': [], 'checks': []}

        def start():
            nonlocal process
            process = subprocess.Popen([sys.executable,'-m','streamlit','run','app.py','--server.headless=true',
                '--server.address=127.0.0.1',f'--server.port={port}','--browser.gatherUsageStats=false'],
                cwd=ROOT,env=env,stdout=log,stderr=log)
            deadline = perf_counter()+30
            while perf_counter()<deadline:
                if process.poll() is not None: raise RuntimeError('Server exited; inspect server.log')
                try:
                    with urlopen(url+'/_stcore/health',timeout=1) as response:
                        if response.status==200: return
                except OSError: sleep(.1)
            raise RuntimeError('Server startup timed out')

        def stop():
            nonlocal process
            if process:
                process.terminate()
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                process=None

        try:
            start()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                result['browser'] = browser.version
                page = browser.new_page(viewport={'width':1440,'height':1800})
                page.set_default_timeout(15000)

                def show_schedule():
                    expect(page.get_by_role('heading',name='Combined schedule',exact=True)).to_be_visible()
                    page.get_by_label('Select a date.',exact=True).fill('2026/10/26')
                    page.get_by_label('Select a date.',exact=True).press('Enter')
                    page.get_by_label('Select a date.',exact=True).press('Escape')
                    page.get_by_role('heading',name='Combined schedule',exact=True).click()
                    expect(page.get_by_role('heading',name='Weekly schedule: 2026-10-26 to 2026-11-01',exact=True)).to_be_visible()

                def choose_task(identifier):
                    page.get_by_label(re.compile(r'Task to correct$')).click()
                    page.get_by_role('option',name=re.compile(rf'^#{identifier} —')).click()
                    saved = next(row for row in repository.restore_saved_application_state()['tasks'] if row['id']==identifier)
                    expect(page.get_by_label('New start time',exact=True)).to_have_value(saved['start_time'])
                    expect(page.get_by_label('New end time',exact=True)).to_have_value(saved['end_time'])

                def fill_times(start_time,end_time):
                    page.get_by_label('New start time',exact=True).fill('2026-10-26T'+start_time)
                    page.get_by_label('New end time',exact=True).fill('2026-10-26T'+end_time)

                def capture(name):
                    # Streamlit scrolls inside its app container; focus this evidence on the schedule.
                    page.get_by_role('heading',name='Combined schedule',exact=True).evaluate("node => node.scrollIntoView({block: 'start'})")
                    page.screenshot(path=str(OUT / name),full_page=True)

                page.goto(url)
                page.get_by_label('Course',exact=True).fill('CS 491')
                page.get_by_label('Assignment name',exact=True).fill('Integrated schedule review')
                page.get_by_label('Due date (YYYY-MM-DD)',exact=True).fill('2026-10-30')
                page.get_by_role('button',name='Save coursework',exact=True).click()
                expect(page.get_by_text('Coursework saved.',exact=True)).to_be_visible()
                page.locator('input[type=file]').set_input_files({'name':'context.csv','mimeType':'text/csv',
                    'buffer':b'course,item_name,due_date\nCS 310,Imported context,2026-10-30\n'})
                page.get_by_role('button',name='Import coursework',exact=True).click()
                expect(page.get_by_text('Accepted: 1; rejected: 0',exact=True)).to_be_visible()
                result['checks'].append('PASS real manual and CSV coursework entry persisted')
                course = repository.restore_saved_application_state()['coursework'][0]
                a, b = add_sample_plans(repository,course['id'])
                result['fixture_counts'] = {key:len(rows) for key,rows in repository.restore_saved_application_state().items()}
                result['database_bytes_start'] = path.stat().st_size

                for run in range(3):
                    # Re-create the saved overlap through the plan repository, never automatic UI repair.
                    repository.StorePlanData(**a)
                    page.reload()
                    show_schedule()
                    expect(page.get_by_text(re.compile(r'^Conflict: Task #1'))).to_be_visible()
                    expect(page.get_by_text(re.compile(r'^Conflict: Task #2'))).to_be_visible()
                    if run==0:
                        capture('01-saved-conflicts.png')
                        page.get_by_text('Daily',exact=True).click()
                        expect(page.get_by_role('heading',name='Daily schedule: 2026-10-26 to 2026-10-26',exact=True)).to_be_visible()
                        capture('02-daily-conflicts.png')
                        page.get_by_text('Weekly',exact=True).click()
                    choose_task(2)
                    fill_times('10:15','11:45')
                    before = repository.restore_saved_application_state()
                    begin=perf_counter()
                    page.get_by_role('button',name='Save corrected times',exact=True).click()
                    expect(page.get_by_text('times: Proposed times conflict with the tasks below. Saved times were not changed.',exact=True)).to_be_visible()
                    expect(page.get_by_text(re.compile(r'^Task #1 — Review \|'))).to_be_visible()
                    expect(page.get_by_text(re.compile(r'^Task #4 — Review \|'))).to_be_visible()
                    result['conflict_seconds'].append(perf_counter()-begin)
                    assert repository.restore_saved_application_state()==before
                    if run==0: capture('03-rejected-correction.png')
                    fill_times('12:00','13:00')
                    begin=perf_counter()
                    page.get_by_role('button',name='Save corrected times',exact=True).click()
                    expect(page.get_by_text('Task #2 saved: 2026-10-26T12:00 → 2026-10-26T13:00.',exact=True)).to_be_visible()
                    expect(page.get_by_text('No conflicts in this period.',exact=True)).to_be_visible()
                    result['correction_seconds'].append(perf_counter()-begin)
                    assert all(not task['conflict_ids'] for task in ScheduleService(repository).get_schedule()['tasks'])
                result['checks'].append('PASS C8/C9 saved overlaps identify all affected tasks; three rejected and three accepted corrections')
                capture('04-resolved.png')
                choose_task(1)
                fill_times('09:00','10:00')
                page.get_by_role('button',name='Save corrected times',exact=True).click()
                expect(page.get_by_text('Task #1 saved: 2026-10-26T09:00 → 2026-10-26T10:00.',exact=True)).to_be_visible()
                # C7 deletion through the plan-owned aggregate interface.
                changed = repository.get_plan(1)
                changed['tasks'] = [row for row in changed['tasks'] if row['id']!=2]
                changed['plan']['notes'] = 'Latest revision from the plan fixture; no export/revision UI available.'
                repository.StorePlanData(**changed)
                page.get_by_role('button',name='Refresh schedule',exact=True).click()
                expect(page.get_by_label(re.compile(r'Task to correct$'))).to_be_visible()
                page.get_by_label(re.compile(r'Task to correct$')).click()
                expect(page.get_by_role('option',name=re.compile(r'^#2 —'))).to_have_count(0)
                page.keyboard.press('Escape')
                expected = repository.RestoreSavedApplicationState()
                (OUT/'before-restart.json').write_text(json.dumps(expected,indent=2))
                stop()
                start()
                page.close()
                page=browser.new_page(viewport={'width':1440,'height':1800})
                page.goto(url)
                show_schedule()
                expect(page.get_by_text('No conflicts in this period.',exact=True)).to_be_visible()
                actual = open_application(path)[0].RestoreSavedApplicationState()
                assert actual==expected
                assert repository.get_plan(2)==b
                choose_task(1)
                expect(page.get_by_label('New start time',exact=True)).to_have_value('2026-10-26T09:00')
                capture('05-after-restart.png')
                (OUT/'after-restart.json').write_text(json.dumps(actual,indent=2))
                result['checks'].append('PASS C7/N3 actual Streamlit process restart preserves corrected A1 ID/plan, deleted A2, unchanged B1')
                # Changes made by the owning plan screen must immediately affect the next schedule read.
                repository.StorePlanData({**b['plan'],'active':False})
                page.get_by_role('button',name='Refresh schedule',exact=True).click()
                page.get_by_label(re.compile(r'Task to correct$')).click()
                expect(page.get_by_role('option',name=re.compile(r'^#4 —'))).to_have_count(0)
                page.keyboard.press('Escape')
                repository.StorePlanData(b['plan'])
                repository.delete_plan(1)
                page.get_by_role('button',name='Refresh schedule',exact=True).click()
                expect(page.get_by_role('combobox',name=re.compile(r'^Selected #4 .*Task to correct$'))).to_be_visible()
                expect(page.get_by_label('New start time',exact=True)).to_have_value('2026-10-26T11:00')
                capture('06-plan-deleted.png')
                assert [row['id'] for row in ScheduleService(repository).get_schedule()['tasks']]==[4]
                result['checks'].append('PASS active-plan filtering and explicit plan deletion reflected in real schedule')
                with sqlite3.connect(path) as source, sqlite3.connect(OUT/'academic-state.sqlite3') as destination:
                    assert source.execute('PRAGMA foreign_key_check').fetchall()==[]
                    source.backup(destination)
                result['database_bytes_end'] = path.stat().st_size
                result['source_sha256'] = {str(file.relative_to(ROOT)):hashlib.sha256(file.read_bytes()).hexdigest()
                    for file in [ROOT/'app.py',ROOT/'demos/src/scheduling.py',*sorted((ROOT/'folio').glob('*.py')),Path(__file__).resolve()]}
                assert all(value<2 for value in result['correction_seconds']+result['conflict_seconds'])
                result['status']='PASS'
                browser.close()
        except Exception as error:
            result.update(status='FAIL',error=str(error))
            raise
        finally:
            stop()
            log.close()
            (OUT/'browser-results.json').write_text(json.dumps(result,indent=2))
            print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
