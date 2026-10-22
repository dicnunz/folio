"""Real Streamlit/Chromium verification using only a disposable database.

Run: python -m scripts.verify_cse22_browser
Writes screenshots, SQL snapshots, timings and server output to evidence/cse-22.
"""
import json
import hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
import os
from pathlib import Path
import platform
import socket
import sqlite3
import subprocess
import sys
import tempfile
from time import perf_counter, sleep
from urllib.request import urlopen

from playwright.sync_api import sync_playwright, expect
from folio.application import open_application
from scripts.seed_academic_fixture import seed

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence' / 'cse-22'


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='folio-cse22-browser-') as directory:
        database = Path(directory) / 'academic.sqlite3'
        seed(database)
        repository, _ = open_application(database)
        with socket.socket() as port_socket:
            port_socket.bind(('127.0.0.1', 0))
            port = port_socket.getsockname()[1]
        url = f'http://127.0.0.1:{port}'
        environment = {**os.environ, 'FOLIO_DATABASE': str(database), 'PYTHONDONTWRITEBYTECODE': '1'}
        timings = {'coursework_save': [], 'stored_plan_display': []}
        metadata = {'recorded_at': datetime.now(ZoneInfo('America/New_York')).isoformat(),
                    'platform': platform.platform(), 'python': platform.python_version(),
                    'sqlite': sqlite3.sqlite_version, 'database_bytes_start': database.stat().st_size,
                    'timing': 'perf_counter around Playwright click through visible result assertion',
                    'base_commit': subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                    'implementation': 'local CSE-22 working tree; see source hashes'}
        process = None
        log = (EVIDENCE / 'streamlit-server.log').open('w')

        def start():
            nonlocal process
            process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'app.py',
                '--server.headless=true', '--server.address=127.0.0.1', f'--server.port={port}',
                '--browser.gatherUsageStats=false'], cwd=ROOT, env=environment, stdout=log, stderr=log)
            deadline = perf_counter() + 30
            while perf_counter() < deadline:
                if process.poll() is not None:
                    raise RuntimeError('Streamlit exited; inspect server log')
                try:
                    with urlopen(url + '/_stcore/health', timeout=1) as response:
                        if response.status == 200:
                            return
                except OSError:
                    sleep(.1)
            raise RuntimeError('Streamlit startup timed out')

        def stop():
            nonlocal process
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                process = None

        try:
            start()
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                metadata['browser'] = browser.version
                page = browser.new_page(viewport={'width': 1440, 'height': 1100})
                page.set_default_timeout(15000)
                page.goto(url)
                expect(page.get_by_role('heading', name='Folio', exact=True)).to_be_visible()
                page.get_by_role('button', name='Save coursework', exact=True).click()
                expect(page.get_by_text('course: course is required.', exact=True)).to_be_visible()
                expect(page.get_by_text('item_name: item_name is required.', exact=True)).to_be_visible()
                expect(page.get_by_text('due_date: due_date is required.', exact=True)).to_be_visible()
                page.screenshot(path=str(EVIDENCE / 'validation.png'), full_page=True)

                for run in range(3):
                    page.reload()
                    page.get_by_label('Course', exact=True).fill('Browser course')
                    page.get_by_label('Assignment name', exact=True).fill(f'Browser saved {run}')
                    page.get_by_label('Due date (YYYY-MM-DD)', exact=True).fill('2026-10-26')
                    start_time = perf_counter()
                    page.get_by_role('button', name='Save coursework', exact=True).click()
                    expect(page.get_by_text('Coursework saved.', exact=True)).to_be_visible()
                    timings['coursework_save'].append(perf_counter() - start_time)
                    assert any(row['item_name'] == f'Browser saved {run}' for row in repository.restore_saved_application_state()['coursework'])
                    page.screenshot(path=str(EVIDENCE / 'coursework-saved.png'), full_page=True)

                # Real CSV upload, mixed row errors, and committed values.
                page.locator('input[type=file]').set_input_files({'name': 'mixed.csv', 'mimeType': 'text/csv',
                    'buffer': b'course,item_name,due_date\nImported,CSV record,2026-10-26\nImported,,bad\nImported,CSV record,2026-10-26\n'})
                page.get_by_role('button', name='Import coursework', exact=True).click()
                expect(page.get_by_text('Accepted: 1; rejected: 2', exact=True)).to_be_visible()
                page.screenshot(path=str(EVIDENCE / 'csv-import.png'), full_page=True)

                for _ in range(3):
                    page.reload()
                    expect(page.get_by_role('button', name='Open saved plan', exact=True)).to_be_visible()
                    start_time = perf_counter()
                    page.get_by_role('button', name='Open saved plan', exact=True).click()
                    expect(page.get_by_role('heading', name='Plan A', exact=True)).to_be_visible()
                    expect(page.get_by_role('heading', name='Entered feedback', exact=True)).to_be_visible()
                    timings['stored_plan_display'].append(perf_counter() - start_time)
                page.screenshot(path=str(EVIDENCE / 'saved-plan.png'), full_page=True)

                # Update using the existing coursework controls (fixture coursework is selected).
                page.get_by_label('Edit assignment name', exact=True).fill('Revised before restart')
                page.get_by_role('button', name='Save changes', exact=True).click()
                expect(page.get_by_text('Coursework changes saved.', exact=True)).to_be_visible()
                page.get_by_role('button', name='Delete selected coursework', exact=True).click()
                expect(page.get_by_text('_record: Coursework is referenced by plans or tasks; deletion was not performed.', exact=True)).to_be_visible()

                stop()
                state = repository.restore_saved_application_state()
                aggregate = repository.get_plan(state['plans'][0]['id'])
                other_plan = repository.get_plan(state['plans'][1]['id'])
                aggregate['plan']['notes'] = 'Latest saved revision, restored after process restart.'
                aggregate['tasks'] = aggregate['tasks'][:1]  # Remove A2; preserve A1 identity.
                aggregate['tasks'][0].update(start_time='2026-10-24T14:00', end_time='2026-10-24T15:00')
                aggregate['feedback'][0]['adapted_text'] = 'Latest entered feedback'
                repository.StorePlanData(**aggregate)
                expected = repository.RestoreSavedApplicationState()
                (EVIDENCE / 'before-restart.json').write_text(json.dumps(expected, indent=2))
                start()
                page.close()
                page = browser.new_page(viewport={'width': 1440, 'height': 1100})
                page.goto(url)
                expect(page.get_by_label('Edit assignment name', exact=True)).to_have_value('Revised before restart')
                page.get_by_role('button', name='Open saved plan', exact=True).click()
                expect(page.get_by_text('Latest saved revision, restored after process restart.', exact=True)).to_be_visible()
                page.screenshot(path=str(EVIDENCE / 'restored-after-restart.png'), full_page=True)
                restored_repository, _ = open_application(database)
                actual = restored_repository.RestoreSavedApplicationState()
                assert actual == expected
                assert restored_repository.get_plan(state['plans'][1]['id']) == other_plan
                with sqlite3.connect(database) as connection:
                    assert connection.execute('PRAGMA foreign_key_check').fetchall() == []
                (EVIDENCE / 'after-restart.json').write_text(json.dumps(actual, indent=2))
                with sqlite3.connect(database) as source, sqlite3.connect(EVIDENCE / 'academic-state.sqlite3') as destination:
                    source.backup(destination)
                metadata['source_sha256'] = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in [ROOT / 'app.py', *sorted((ROOT / 'folio').glob('*.py')), Path(__file__).resolve()]}
                metadata['database_bytes_end'] = database.stat().st_size
                metadata['counts_after_restart'] = {name: len(rows) for name, rows in actual.items()}
                metadata['timings_seconds'] = timings
                metadata['status'] = 'PASS'
                # Preserve actual measurements even when a performance assertion fails.
                (EVIDENCE / 'browser-results.json').write_text(json.dumps(metadata, indent=2))
                assert all(value < 2 for values in timings.values() for value in values)
                browser.close()
                print(json.dumps(metadata, indent=2))
        except Exception as error:
            metadata.update(status='FAIL', error=str(error), timings_seconds=timings)
            (EVIDENCE / 'browser-results.json').write_text(json.dumps(metadata, indent=2))
            raise
        finally:
            stop()
            log.close()


if __name__ == '__main__':
    main()
