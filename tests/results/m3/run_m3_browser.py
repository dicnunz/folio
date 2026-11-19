"""M3 supplemental real browser checks; only temporary databases are modified.
Run from repository root: /tmp/folio-m3-venv/bin/python tests/results/m3/run_m3_browser.py
Results distinguish observed defects from harness errors; no mock notifications.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import json, os, platform, socket, sqlite3, subprocess, tempfile, traceback
from datetime import datetime
from zoneinfo import ZoneInfo
from time import perf_counter, sleep
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect
from folio.application import open_application
from scripts.seed_schedule_fixture import seed
OUT = Path(__file__).resolve().parent / 'browser-m3'
OUT.mkdir(exist_ok=True)
result = {'recorded_at': datetime.now(ZoneInfo('America/New_York')).isoformat(),
          'python': platform.python_version(), 'platform': platform.platform(),
          'sqlite': sqlite3.sqlite_version, 'checks': [], 'csv_500_seconds': [],
          'method': 'perf_counter before Import coursework click until fresh visible accepted/rejected result and Import processed confirmation; upload excluded'}
def check(name, passed, observed):
    result['checks'].append({'id': name, 'status': 'PASS' if passed else 'FAIL', 'observed': observed})
with tempfile.TemporaryDirectory(prefix='folio-m3-browser-') as folder:
    db = Path(folder) / 'academic.sqlite3'
    seed(db)
    repo, service = open_application(db)
    result['database_bytes_start'] = db.stat().st_size
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    log = (OUT / 'server.log').open('w')
    proc = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.headless=true',
        '--server.address=127.0.0.1', f'--server.port={port}', '--browser.gatherUsageStats=false'],
        cwd=ROOT, env={**os.environ, 'FOLIO_DATABASE': str(db)}, stdout=log, stderr=log)
    try:
        for _ in range(300):
            try:
                with urlopen(url + '/_stcore/health', timeout=1): break
            except OSError: sleep(.1)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            result['browser'] = browser.version
            page = browser.new_page(viewport={'width': 1440, 'height': 1600})
            page.set_default_timeout(15000)
            page.goto(url)
            def button(name): return page.get_by_role('button', name=name, exact=True)
            def times(start, end):
                page.get_by_label('New start time', exact=True).fill(start)
                page.get_by_label('New end time', exact=True).fill(end)
            def show_date(day):
                field = page.get_by_label('Select a date.', exact=True)
                field.fill(day.replace('-', '/')); field.press('Enter'); field.press('Escape')
                page.get_by_role('heading', name='Combined schedule', exact=True).click()
            def shot(name):
                page.get_by_role('heading', name='Combined schedule', exact=True).evaluate("n => n.scrollIntoView({block:'start'})")
                page.screenshot(path=str(OUT / name), full_page=True)
            show_date('2026-10-26')
            # Remove overlap via fixture to isolate touching and overnight checks.
            a = repo.get_plan(1)
            a['tasks'] = [row for row in a['tasks'] if row['id'] != 2]
            repo.StorePlanData(**a)
            button('Refresh schedule').click()
            expect(page.get_by_text('No conflicts in this period.', exact=True)).to_be_visible()
            check('S-touching', True, 'Task 1 ends at 11:00; task 4 starts at 11:00; UI reports no conflicts.')
            shot('touching.png')
            before = repo.RestoreSavedApplicationState()
            times('invalid', '2026-10-26T11:00')
            button('Save corrected times').click()
            expect(page.locator('[data-testid="stAlert"]').filter(has_text='start_time')).to_be_visible()
            check('E-invalid', repo.RestoreSavedApplicationState() == before, 'Invalid start rejected visibly; entire saved snapshot compared.')
            # Coursework deadline is October 30. November 2 is unambiguously beyond it.
            times('2026-11-02T09:00', '2026-11-02T10:00')
            button('Save corrected times').click()
            expect(page.get_by_text('Task #1 saved: 2026-11-02T09:00 → 2026-11-02T10:00.', exact=True)).to_be_visible()
            after = repo.RestoreSavedApplicationState()
            check('D-deadline-rejection', False, 'UI accepted and persisted task 1 on November 2, after associated coursework due October 30. No deadline validation feedback.')
            check('D-unrelated', [t for t in before['tasks'] if t['id'] != 1] == [t for t in after['tasks'] if t['id'] != 1], 'All unrelated task records unchanged after late save.')
            (OUT / 'deadline-before.json').write_text(json.dumps(before, indent=2))
            (OUT / 'deadline-after.json').write_text(json.dumps(after, indent=2))
            shot('deadline-accepted.png')
            # Select moved task in its new week, then correct it to before deadline.
            show_date('2026-11-02')
            times('2026-10-26T23:00', '2026-10-27T00:30')
            button('Save corrected times').click()
            expect(page.get_by_text('Task #1 saved: 2026-10-26T23:00 → 2026-10-27T00:30.', exact=True)).to_be_visible()
            check('D-valid-correction', repo.get_plan(1)['tasks'][0]['start_time']=='2026-10-26T23:00', 'Valid pre-deadline overnight correction saved.')
            show_date('2026-10-26')
            page.get_by_text('Daily', exact=True).click()
            expect(page.get_by_role('heading', name='Daily schedule: 2026-10-26 to 2026-10-26', exact=True)).to_be_visible()
            shot('overnight-first-day.png')
            show_date('2026-10-27')
            expect(page.get_by_role('heading', name='Daily schedule: 2026-10-27 to 2026-10-27', exact=True)).to_be_visible()
            # Task selector includes overnight task on both days; verify second-day presence.
            import re
            selector = page.get_by_label(re.compile(r'Task to correct$'))
            selector.click()
            expect(page.get_by_role('option', name=re.compile(r'^#1 —'))).to_be_visible()
            page.keyboard.press('Escape')
            check('S-overnight', True, 'Overnight task saved through UI and available in next day schedule selector.')
            shot('overnight-next-day.png')
            # Forced SQLite write failure exercises actual UI error + transaction rollback.
            before = repo.RestoreSavedApplicationState()
            with sqlite3.connect(db) as c:
                c.execute("CREATE TRIGGER m3_fail BEFORE UPDATE ON tasks BEGIN SELECT RAISE(ABORT,'M3 injected write failure'); END")
            times('2026-10-27T08:00', '2026-10-27T09:00')
            button('Save corrected times').click()
            expect(page.locator('[data-testid="stAlert"]').filter(has_text='storage:')).to_be_visible()
            check('E-write-failure', repo.RestoreSavedApplicationState()==before, 'Actual SQLite trigger rejected write; UI storage error visible; saved snapshot unchanged.')
            shot('write-failure.png')
            with sqlite3.connect(db) as c: c.execute('DROP TRIGGER m3_fail')
            # Simulate another session editing the displayed task before this form submits.
            times('2026-10-27T07:00', '2026-10-27T08:00')
            changed = repo.get_plan(1)
            changed['tasks'][0].update(start_time='2026-10-27T06:00', end_time='2026-10-27T07:00')
            repo.StorePlanData(**changed)
            stale_before = repo.RestoreSavedApplicationState()
            button('Save corrected times').click()
            expect(page.get_by_label('New start time', exact=True)).to_have_value('2026-10-27T06:00')
            check('E-stale-preservation', repo.RestoreSavedApplicationState()==stale_before,
                  'External fixture update preserved when stale browser form submitted; UI reset to latest saved interval.')
            result['stale_ui_alerts'] = page.locator('[data-testid="stAlert"]').all_text_contents()
            shot('stale-update.png')
            result['available_buttons'] = page.get_by_role('button').all_text_contents()
            result['completion_reminder_controls'] = 'No completion, undo, progress or reminder controls in app.py/schedule_ui.py or observed UI; not executable.'
            for run in range(3):
                page.reload()
                rows = 'course,item_name,due_date\n' + ''.join(f'M3 import {run},Record {i},2026-12-01\n' for i in range(500))
                (OUT / f'import-500-{run+1}.csv').write_text(rows)
                page.locator('input[type=file]').set_input_files({'name':f'import-{run}.csv','mimeType':'text/csv','buffer':rows.encode()})
                expect(button('Import coursework')).to_be_enabled()
                expect(page.get_by_text('Accepted: 500; rejected: 0', exact=True)).to_have_count(0)
                start = perf_counter()
                button('Import coursework').click()
                expect(page.get_by_text('Accepted: 500; rejected: 0', exact=True)).to_be_visible()
                expect(page.get_by_text('Import processed.', exact=True)).to_be_visible()
                result['csv_500_seconds'].append(perf_counter()-start)
                records = repo.RestoreSavedApplicationState()['coursework']
                assert sum(r['course']==f'M3 import {run}' for r in records)==500
            check('P-import-500', max(result['csv_500_seconds']) <= 5, 'Three real UI imports accepted 500 distinct rows each; persisted counts checked.')
            page.screenshot(path=str(OUT / 'import-500.png'), full_page=True)
            with sqlite3.connect(db) as c:
                check('E-integrity', c.execute('PRAGMA integrity_check').fetchone()[0]=='ok' and not c.execute('PRAGMA foreign_key_check').fetchall(), 'SQLite integrity and foreign-key checks passed.')
            result['counts_end'] = {k:len(v) for k,v in repo.RestoreSavedApplicationState().items()}
            result['database_bytes_end'] = db.stat().st_size
            result['status'] = 'COMPLETED_WITH_DEADLINE_DEFECT'
            browser.close()
    except Exception:
        result['status']='HARNESS_ERROR'
        result['error']=traceback.format_exc()
        raise
    finally:
        proc.terminate()
        try: proc.wait(timeout=10)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        log.close()
        (OUT/'results.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))
