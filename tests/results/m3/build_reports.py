"""Derive M3 reports from retained execution artifacts; no synthetic timings."""
from pathlib import Path
import json, statistics, xml.etree.ElementTree as ET
OUT=Path(__file__).resolve().parent
r22=json.loads((OUT/'browser-cse22/browser-results.json').read_text())
r23=json.loads((OUT/'browser-cse23/browser-results.json').read_text())
r3=json.loads((OUT/'browser-m3/results.json').read_text())
def write(name, text): (OUT/name).write_text(text.strip()+'\n')
rows=[]
for name, file in [('Existing application','application.xml'),('Existing demos','demos.xml'),('New M3 regression assertions','m3-regressions.xml')]:
    a=ET.parse(OUT/file).getroot().find('testsuite').attrib
    n,f,e,s=map(lambda k:int(a[k]),['tests','failures','errors','skipped'])
    rows.append(f"| {name} | {n} | {n-f-e-s} | {f} | {e} | {s} | {a['time']} s | {file} |")
write('test-summary.md', '''# M3-11 execution summary

Executed November 18, 2026 (America/New_York), commit `6a6c3cc94cf6e6d4fdb91fd9098ab98c2218c6e5`. This checkout identifies itself as the M2 local app. M3 acceptance is **not complete**: deadline enforcement fails and multiple required workflows are not implemented.

| Suite | Executed | Passed | Failed | Errors | Skipped | JUnit duration | Evidence |
|---|---:|---:|---:|---:|---:|---:|---|
'''+ '\n'.join(rows)+'''

**143 unique pytest cases: 142 passed, 1 failed, 0 skipped, 0 collection errors on final runs.** Existing baseline: 140/140 passed before supplemental tests were added. Blocked acceptance workflows are not pytest skips and are listed separately in acceptance-matrix.md. Two existing browser scenarios passed. Supplemental browser checks have one observed deadline defect; see functional-results.md. Browser assertions are not added to the pytest total. Repeated executions are not counted twice.

## Repository and setup

- Python app: `app.py`, `folio/` (SQLite repository, application composition, coursework and schedule Streamlit UI/service); reused domain services in `demos/src/`.
- Streamlit 1.49.1 serves both frontend and backend in one process; no separate production frontend build. SQLite schema v2; `FOLIO_DATABASE` selects database, otherwise `data/academic.sqlite3`. All testing used temporary paths. No production database was opened.
- pytest 9.1.1: `tests/` application/domain/integration tests including Streamlit AppTest, and `demos/tests/` standalone M1 domain tests. Playwright 1.64.0: existing real-browser scripts `scripts/verify_cse22_browser.py`, `scripts/verify_cse23_browser.py`.
- No pytest config or AGENTS.md was found in the repository scan. The demo suite requires its own working directory for `src` imports. `requirements-dev.txt` includes runtime requirements. Exact resolved packages: environment-packages.txt.
- `testing/folio-tool-evaluation/` contains historical comparison prototypes (Flask, Django, React/TypeScript, tinyfolio, alternate CSV/storage/export libraries). These are not connected to `app.py`; not executed or counted as M3 application tests. `docs/` is the static project website, not the app.
- Acceptance definitions: `docs/documents/first-semester/milestone-1/test.pdf`, extracted to acceptance-source.txt. No existing deadline-validation case was located; supplemental D identifiers are local to this report.

## Commands and recovery

Initial README commands `.venv/bin/python -m pytest tests -v` (root) and `../.venv/bin/python -m pytest tests -v` (demos) failed before collection: `No module named pytest`. Original logs: application.log, demos.log. Existing venv points to Python 3.14; isolated Python 3.11 environment created instead.

```sh
python3.11 -m venv /tmp/folio-m3-venv
/tmp/folio-m3-venv/bin/python -m pip install -r requirements-dev.txt pypdf
/tmp/folio-m3-venv/bin/python -m pytest tests -v --junitxml=tests/results/m3/application.xml
# From demos/:
/tmp/folio-m3-venv/bin/python -m pytest tests -v --junitxml=../tests/results/m3/demos.xml
# From root, after baseline execution:
/tmp/folio-m3-venv/bin/python tests/results/m3/run_existing_browser.py
/tmp/folio-m3-venv/bin/python -m pytest tests/results/m3/test_m3_regressions.py -v --junitxml=tests/results/m3/m3-regressions.xml
/tmp/folio-m3-venv/bin/python tests/results/m3/run_m3_browser.py
```

Outputs are retained in application-rerun.log, demos-rerun.log, existing-browser.log, m3-regressions.log and m3-browser.log. The added test file is under tests/, so future root suite runs will also collect its known failing deadline assertion. To reproduce only the original baseline, pass the five original `tests/test_*.py` files explicitly.

Dependency installation initially failed due sandbox DNS restrictions (dependency-install.log); an approved network retry succeeded (dependency-install-retry.log). Browser startup initially could not bind localhost in the sandbox; approved local execution succeeded using cached Chromium. The application suite was also rerun outside the sandbox. These are recovered environment issues, not product defects. No runtime source was edited; generated changes to tracked bytecode caches were restored.

Launch a review app using a new fixture path:

```sh
/tmp/folio-m3-venv/bin/python -m scripts.seed_schedule_fixture /tmp/folio-m3-review.sqlite3
FOLIO_DATABASE=/tmp/folio-m3-review.sqlite3 /tmp/folio-m3-venv/bin/python -m streamlit run app.py
```

Choose October 26, 2026. Fixture creation refuses an existing path. Browser runners create their own temporary databases, terminate their servers, and preserve snapshots/screenshots under this directory. Historical evidence directories were not overwritten.
''')
checks='\n'.join(f"| {c['id']} | {c['status']} | {c['observed']} | browser-m3/results.json |" for c in r3['checks'])
write('functional-results.md','''# M3 functional results

Statuses apply only to the stated scope. Fixture-assisted setup/deletion uses real repository writes against disposable SQLite; it is not proof that a missing plan editor exists. Streamlit AppTest is not a browser measurement. No reminder mocks or simulated screenshots were used.

| Requirement | Procedure / expected behavior | Observed / status | Evidence |
|---|---|---|---|
| A: F12–14, F42–45; completion/undo/progress | Complete A1 twice, complete A2, undo A1; display 0/50/50/100/50%, leave B unchanged, show congratulations | BLOCKED: no connected completion or undo controls, progress calculation/bar, or congratulatory response | app.py; folio/schedule_ui.py; browser-m3/results.json |
| A: completion flag persistence | Repeated boolean changes and reopening preserve task state and other plan | PASS, repository-only: true/true/false/true/false persisted; does not verify progress | test_m3_regressions.py; m3-regressions.log |
| A: actual restart | Stop/start Streamlit with same DB; restore most recent academic state | PASS, academic subset; full snapshots equal, IDs and other plan preserved | browser-cse22/before-restart.json and after-restart.json; browser-cse23 equivalent; screenshots |
| A: duplicate rewards | Repeated completion, undo/recomplete, refresh/restart must not duplicate reward | BLOCKED in application; demo reward unit tests pass but are not connected persistent rewards | demos-rerun.log; demos/src/rewards.py; app.py |
| B: F11 reminder configure/change/disable/persist/deliver | Configure due reminder, restart, observe real due delivery and invalid-time feedback | BLOCKED: no reminder settings schema, scheduler or delivery UI in connected app. Whether it must remain running is UNVERIFIED; no delivery claim | folio/storage.py; app.py; folio/schedule_ui.py |
| C: F34–41/I10–11 scheduling | Overlaps identify tasks; touching intervals clear; overnight tasks span days; correction persists | PASS for existing schedule/correction path; creation uses explicit fixture, not unavailable task editor | tests/test_combined_schedule.py; tests/test_schedule_ui.py; browser-cse23 and browser-m3 |
| C: deletion/active plans | Removed tasks/plans disappear without altering unrelated records | PASS via repository mutation + actual UI refresh and process restart | browser-cse23/browser-results.json; 06-plan-deleted.png |
| D: new deadline validation | Reject preparation moved after linked coursework due date with feedback and no mutation | FAIL: task #1 accepted November 2 after October 30 due date; explicit success feedback | browser-m3/deadline-accepted.png; deadline-before.json; deadline-after.json; m3-regressions.log |
| D: valid correction/unrelated records | Save pre-deadline interval and leave other tasks unchanged | PASS: overnight correction saved; unrelated task snapshots equal | browser-m3/results.json; m3-regressions.log |
| E: invalid inputs | Reject invalid times/coursework with useful feedback; preserve saved data | PASS: browser invalid start + empty coursework; automated malformed/equal/reversed times and import validation | browser-m3/results.json; browser-cse22/validation.png; application-rerun.log; demos-rerun.log |
| E: failed writes/rollback | Actual write failure shows error and leaves snapshot consistent | PASS: SQLite trigger causes UI storage error and no changes; tests also cover aggregate/delete/commit rollback | browser-m3/write-failure.png; tests/test_combined_schedule.py; tests/test_academic_storage.py |
| E: stale updates | Preserve newer record when stale form submitted | PASS preservation: form resets to latest interval; service rejects explicit stale expected times. Browser does not show dedicated stale warning (usability limitation) | browser-m3/stale-update.png; results.json stale_ui_alerts; test_missing_and_stale_task_preserve_data |
| E: persisted integrity | Foreign keys and SQLite integrity remain valid after scenarios | PASS | browser-m3/results.json; existing browser DB checks |

## Supplemental browser observations

| Check | Status | Observation | Evidence |
|---|---|---|---|
'''+checks+'''

Creation of assessments/preparation tasks is represented by coursework due_date and linked plan tasks; there is no explicit preparation-task type or separate assessment-deadline relation. The deadline test uses a date beyond the entire due day, avoiding same-day cutoff ambiguity. Reminder and completion workflows cannot be evaluated by modifying storage fields alone.
''')
perf=[('Display stored plan',r22['timings_seconds']['stored_plan_display'],2,'browser-cse22/browser-results.json'),
('Update displayed schedule (time correction)',r23['correction_seconds'],2,'browser-cse23/browser-results.json'),
('Detect/display proposed conflicts',r23['conflict_seconds'],2,'browser-cse23/browser-results.json'),
('Confirm saved coursework',r22['timings_seconds']['coursework_save'],2,'browser-cse22/browser-results.json'),
('Validate/import 500 CSV records',r3['csv_500_seconds'],5,'browser-m3/results.json')]
pr='\n'.join(f"| {n} | {' / '.join(f'{x:.6f}' for x in v)} | {statistics.mean(v):.6f} | {max(v):.6f} | ≤ {lim} | {'PASS' if max(v)<=lim else 'FAIL'} | {src} |" for n,v,lim,src in perf)
write('performance-results.md','''# M3 performance results

All five measured operation variants passed their thresholds on this local fixture. This is not a scalability claim or verification of unavailable creation/deletion editor and plan-save workflows.

| Operation | Runs 1 / 2 / 3 (seconds) | Mean (s) | Maximum (s) | Limit (s) | Result | Raw evidence |
|---|---|---:|---:|---:|---|---|
'''+pr+f'''

Environment: {r3['platform']}; Python {r3['python']}; SQLite {r3['sqlite']}; Streamlit 1.49.1; Playwright 1.64.0; headless Chromium {r3['browser']}. Local HTTP/loopback, no remote backend. Browser viewports: 1440×1100 (CSE22), 1440×1800 (CSE23), 1440×1600 (supplement). Application commit and source hashes are retained in existing browser JSON. Runs occurred November 18, 2026 America/New_York. Package versions are in environment-packages.txt. Machine model/CPU frequency were not captured; OS/architecture are recorded.

## Measurement method and fixtures

`perf_counter` starts immediately before Playwright submits a button click and ends after fresh result visibility assertions. Browser action/wait overhead is included. These are end-user UI measurements, not service-only timers. Database verification occurs after the timing endpoint. No mocked rendering or fabricated timing is used.

- Plan: `seed_academic_fixture`, initially one coursework, two plans/four tasks/two feedback entries, 40,960-byte SQLite. Three coursework saves and one accepted mixed-import row precede plan reads (five coursework records); each plan request begins after page reload. Endpoint: Plan A heading and Entered feedback visible.
- Save confirmation: three distinct coursework names, click Save coursework through visible Coursework saved; each saved row then checked via repository. Same small academic fixture.
- Schedule/conflict: two coursework, two plans/four tasks/one feedback, 40,960-byte SQLite. Overlap recreated via repository before each trial. Conflict measurement: rejected proposed 10:15–11:45 with both affected tasks displayed. Schedule measurement: accepted 12:00–13:00 correction through saved confirmation and No conflicts in this period. The latter is a rendered schedule-result endpoint; it does not measure individual canvas-cell paint timing. Functional table values/indicators are separately checked with AppTest and screenshots. No UI creation/deletion performance was measured because those editors are absent.
- CSV: three files of exactly 500 unique valid rows (`browser-m3/import-500-1.csv` through `-3.csv`). Each trial reloads to clear prior feedback and uploads before timing; endpoint is Accepted: 500; rejected: 0 plus Import processed. Course prefixes differ per run, so no duplicates. Same disposable DB grows from 1 to 501/1001/1501 coursework records; two plans/three tasks/one feedback remain. DB grows from 40,960 to 184,320 bytes. Every trial's 500 persisted records are counted.

Backend-only timing exists in `test_storage_timing_three_runs`; its passing thresholds are not substituted for browser evidence. Tests run with pytest capture; authoritative acceptance timing comes from the retained browser JSON above.

## Reproduction and manual extension

Run the two browser runners from test-summary.md. For unavailable operation variants once implemented: use a new disposable seeded database; record OS/browser/app commit and data size; time from submit/click to visibly updated table or confirmation using browser tracing or timestamped screen recording; repeat three times with fresh distinct data, retain each sample and compute mean/max. For task creation/deletion, ensure the changed row appears/disappears before stopping the timer. For import, upload first, then time Import through accepted/rejected result and verify all 500 rows. Do not use repository-only timers to claim UI performance.
''')
write('acceptance-matrix.md','''# M3 acceptance matrix

Source: `docs/documents/first-semester/milestone-1/test.pdf` (acceptance-source.txt). These are planned definitions, not historical passes. Requirements IDs below follow that document; performance numbering differs from the Markdown requirements draft, so operation names are authoritative. PASS is limited to the executed scope stated here. BLOCKED means required integrated functionality is unavailable, not a skipped pytest case. Fixtures substitute for absent setup/editing screens only where explicitly stated.

| Case / requirements | Procedure and expected result | Observed result | Status | Evidence |
|---|---|---|---|---|
| N3 / F8–10 | Daily/weekly A1/A2/B1, move A1 to 09:00, reject B1 overlap, preserve identity | Domain exact fixture passes; real browser daily/weekly display, correction/rejection and restart pass | PASS, fixture-assisted | test_n3_daily_weekly_and_rejected_correction; application-rerun.log; browser-cse23 |
| N4 / F11 | Enable/change/disable reminder, observe due delivery, reject 25:00 and preserve setting | Reminder configuration/persistence/delivery not implemented in connected app | BLOCKED, unimplemented | functional-results.md B; app.py; folio/storage.py |
| N5 / F12–14, P3 | 0/50/50/100/50% completion, congratulations, other-plan isolation, empty-plan zero, reopening | Only completion storage flags exist; UI/progress workflow absent | BLOCKED, unimplemented | m3-regressions.log (repository subset only); app.py |
| N6 / F15–16, F48–52 | Full planning with no instructor and rewards disabled; preserve records | Viewing/rescheduling work, but plan creation/editing/completion and optional-feature toggle unavailable | BLOCKED, partial implementation | browser-cse22; browser-cse23; README planned functionality |
| N7 / F17 | Low score/overdue context; no inferred external effort; complete changes only in-app status | Full low-score/overdue acceptance procedure not executed; completion unavailable | NOT-TESTED, blocked dependency | app.py; functional-results.md |
| C6 / F31–32, P1–3 | Restore changed coursework/plans/tasks/completion/rewards and matching progress; fresh DB empty | Academic snapshots and fresh DB pass; game/reward persistence and displayed progress unavailable | BLOCKED for full case; academic subset PASS | test_c6_latest_academic_state_across_process_restart; browser-cse22 before/after-restart.json |
| C7 / F33–35, F40–41, I10 | Same task names retain IDs/plans; reschedule/delete/restart leaves B intact | Passed repository mutation + UI refresh/restart; owning deletion UI absent | PASS, fixture-assisted | tests/test_combined_schedule.py; browser-cse23/05-after-restart.png and 06-plan-deleted.png |
| C8 / F36–38, I11 | Seven interval cases, different date, same/cross plan; touching clear, indicators on both tasks | All 14 interval permutations and date/inactive checks pass; representative real UI conflicts and touching verified | PASS, automated matrix + representative browser | test_c8_every_interval_within_and_across_plans; test_daily_weekly_conflict_indicators_and_student_resolution; browser-m3/touching.png |
| C9 / F37–39, I11 | A2 10:30–11:30 conflicts with A1/B1; move to 12–13, clear indicators | All conflicts identified; rejected proposal unchanged; correction clears conflicts in UI | PASS, fixture-assisted initial creation | browser-cse23/01-saved-conflicts.png, 03-rejected-correction.png, 04-resolved.png |
| C10 / F42, F44–45, P3 | Complete/repeat/complete/undo changes only A progress; restore display | Storage subset passes; completion UI and per-plan progress absent | BLOCKED, unimplemented | m3-regressions.log; app.py |
| C12 / F46, F48 | Mutate rewards, disable features, compare academic state, continue planning/completion | No connected game/reward state or disable toggle; cannot execute full case | BLOCKED, deferred integration | demos/src/rewards.py versus app.py/folio/storage.py |
| C13 / response times | Three visible timings each, 2s operations and 5s 500-row import | Five supported operation variants meet limits; missing editor variants not measured | PASS for measured variants only | performance-results.md; three browser JSON files |
| D1 (new) | Move preparation past linked assessment due date; meaningful rejection and no mutation | November 2 accepted after October 30 deadline | FAIL | m3-regressions.log; browser-m3/deadline-accepted.png |
| D2 (new) | Valid pre-deadline correction saves | October 26–27 overnight correction saved | PASS | browser-m3/results.json; m3-regressions.log |
| D3 (new) | Unrelated tasks unchanged after scheduling attempt | Entire unrelated task collection unchanged | PASS | browser-m3/deadline-before.json and deadline-after.json |

Requested original cases: 5 scoped passes (N3, C7, C8, C9, measured C13), 6 blocked full cases, 1 not-tested case (N7). No blanket M3 acceptance pass. Three new deadline checks: 2 pass, 1 fail. A reward duplicate-event demo pass does not satisfy C11 or the requested connected reward lifecycle; that integration remains blocked.
''')
write('failures.md','''# M3 failures, gaps and recommended fixes

## M3-D1 — Deadline enforcement missing (FAIL; production change required)

Reproduction: seed a disposable schedule fixture. Coursework #1 is due 2026-10-30; linked Plan A task #1 starts October 26. In Combined schedule, move task #1 to 2026-11-02T09:00–10:00 and save. Expected: reject with deadline explanation, preserve original interval and other records. Actual: UI displays `Task #1 saved: 2026-11-02T09:00 → 2026-11-02T10:00.`; database persists it. Screenshot deadline-accepted.png includes both due date and success text. Valid correction back before deadline succeeds; unrelated tasks remain unchanged.

Evidence: browser-m3/deadline-before.json, deadline-after.json, deadline-accepted.png; m3-regressions.log and XML retain the failing assertion and traceback at test_m3_regressions.py:24. Source: folio/schedule_service.py `reschedule_task` checks interval validity, active task existence, stale expected times and overlap but not coursework deadline. Storage accepts the task interval without that constraint. There is no explicit preparation-task type, so the test uses the linked coursework due_date.

Recommended: establish assessment/preparation association and cutoff semantics, validate applicable deadline within the same transaction as rescheduling, cover creation and plan edits, return meaningful UI feedback, preserve snapshot on rejection. Retain the failing regression, add same-day boundary/cross-midnight/deadline-edit coverage when semantics are agreed. No production fix was made.

## Missing completion/progress/reward integration (BLOCKED)

N5, C10 and portions of C6/N6/N7/C12 cannot run. `tasks.completed` persists, but app.py and folio/schedule_ui.py have no completion/undo controls, plan progress bar/calculation or congratulations. Demo reward accounting is separate and does not prove integrated duplicate prevention or persistent reward totals. Implement connected completion transactions, per-plan progress and persistent deduplication before claiming these cases. Repository flag persistence is verified only at its own layer.

## Missing reminders (BLOCKED)

N4 cannot run: no connected configure/change/disable controls, persisted reminder settings, scheduler or delivery mechanism. Delivery, restart restoration and whether Folio must stay running are unverified. Implement and document the lifecycle, then test actual due notifications with the app running and stopped; no mocked notification constitutes acceptance.

## Missing owning editors and optional-feature controls (BLOCKED / limited scope)

Plan/task creation and deletion, full independent planning, reward isolation and disable flows lack connected UI. Test fixtures exercised real repository interfaces and UI refresh, not end-user editor workflows. C7/C9 results must retain the fixture-assisted qualification. Performance does not cover absent editors.

## Stale form feedback limitation (observed)

An external task edit followed by submitting a stale browser form preserves the newer record and resets the form to its current interval. No dedicated stale-change alert was observed (browser-m3/results.json stale_ui_alerts). The service's explicit stale expected-times test passes. Consider retaining displayed version/interval across reruns and showing clear conflict feedback; do not interpret the service test as proof of a visible stale warning.

## Recovered environment issues

Original .venv lacks pytest and uses Python 3.14. Isolated `/tmp/folio-m3-venv` with Python 3.11 and declared dependencies resolved this. Sandbox DNS and localhost-bind restrictions required approved retries. No unresolved environment blocker remains for supported application scenarios. See dependency-install*.log and test-summary.md. Historical library-comparison prototype tests were excluded because they are not connected application tests, not because they passed.
''')
maxima='; '.join(f'{n}: {max(v):.3f}s' for n,v,_,_ in perf)
write('evaluation-evidence.md',f'''# M3 evaluation evidence

On November 18, 2026, the Folio checkout at `6a6c3cc94cf6e6d4fdb91fd9098ab98c2218c6e5` passed all **140 existing automated tests** (64 application, 76 demo). Three supplemental regression assertions produced **2 passes and 1 failure**. No automated cases were skipped. The failure demonstrates that scheduling a linked preparation task after its coursework due date is accepted and persisted. Overall M3 acceptance is therefore **not achieved**.

Real Chromium/Streamlit sessions with disposable SQLite data verified schedule conflicts and correction, touching and overnight intervals, academic restoration after stopping/restarting the actual server, task/plan removal reflected after refresh, invalid-input rejection, write-failure rollback and preservation of a newer record on stale submission. Fixture-assisted plan/task setup and deletion must be disclosed. Completion flags are tested in storage; completion UI, plan progress, reminders and connected persistent rewards are unavailable and are not passing results.

Three measured trials of each supported UI operation met the requested thresholds. Maximum observed durations: {maxima}. Limits were 2 seconds for plan display/schedule update/conflicts/save confirmation and 5 seconds for CSV import. These are local fixture measurements; unavailable editor variants and large schedule scaling were not measured.

Use in the report/presentation:

- Test totals and failure: application.xml, demos.xml, m3-regressions.xml and matching logs.
- Conflict resolution: browser-cse23/01-saved-conflicts.png, 03-rejected-correction.png, 04-resolved.png.
- Real restart evidence: browser-cse23/05-after-restart.png plus before/after-restart.json; browser-cse22 equivalents.
- Deadline defect: browser-m3/deadline-accepted.png and deadline-before/after.json.
- Edge cases/rollback: browser-m3/touching.png, overnight-next-day.png, write-failure.png, stale-update.png.
- Timings: performance-results.md and original browser-results.json/results.json; 500-row fixtures and import screenshot are retained.
- Scope and unavailable cases: acceptance-matrix.md and functional-results.md. Do not present all M3 requirements as complete or demo rewards as connected app acceptance.

All changes are testing/reporting artifacts under tests/results/m3/. Production source and production data were not modified. Historical evidence was preserved.
''')
