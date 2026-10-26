# CSE-23 — combined schedule and conflict correction

Implemented and verified **October 25, 2026** on branch `cbrooks2022/cse-23-m2-combine-active-plan-schedules`. These are actual execution dates, after the October 22 integration target. The schedule feature is connected to the local Streamlit application. The final planning/export/revision walkthrough remains incomplete because those M2 screens have not been located. No slides, commits, pushes, or Linear updates were made.

## Delivered behavior

- Daily and Monday–Sunday weekly views combine dated tasks from every active plan, retaining task IDs, course names, plan names, and plan IDs. Same-name tasks remain distinct.
- Overlaps use `A.start < B.end and A.end > B.start`. Touching endpoints and separate dates do not conflict. Overnight tasks appear in every period they intersect.
- Each affected row identifies its conflicting task IDs. Each warning names both tasks, courses/plans, full intervals, and the overlapping interval.
- Students explicitly choose corrected dates/times. Invalid or conflicting proposals leave saved data unchanged and identify all conflicting tasks. Successful corrections update only the chosen task's interval.
- Plan changes, inactive status, removed tasks, and deleted plans are reflected on the next app interaction or **Refresh schedule**. Saved state is read afresh; startup never inserts sample records.
- Conflict checking and correction run in one write transaction. Failed statements and failed commits roll back. Explicit aggregate plan deletion preserves coursework and other plans.
- The M1 numeric-time scheduling API and demos remain supported. Reminders, completion, progress, rewards, and presentation slides are outside this change.

## Interfaces for the other module owners

| File / API | Contract |
| --- | --- |
| `demos/src/scheduling.py` | `combine_active_tasks(state)` returns `{tasks, errors}` from the academic restoration snapshot. Rows include saved identity/context and `conflict_ids`. It reports malformed active intervals and preserves saved overlaps rather than changing them. `schedule_window(tasks, date, view)` filters Daily/Weekly intervals. |
| `folio/schedule_service.py` | `ScheduleService(repository).get_schedule()` reads current state. `reschedule_task(id, start, end, expected_times=None)` returns `{success, record, errors, conflicts}`; success is reported only after commit. Optional expected times reject stale callers. |
| `folio/schedule_ui.py`, `app.py` | Real combined-schedule screen and correction form, wired after coursework controls. Saved-plan display reads the updated state in the same app run. |
| `folio/storage.py` | Existing `StorePlanData` remains the planning integration point. New `delete_plan(id)` atomically deletes that plan's tasks/feedback and the plan. Transaction methods `academic_state()` and `update_task_times()` support locked checking and narrow updates. No schema migration was needed. |
| `scripts/seed_schedule_fixture.py` | Explicit disposable fixture, or `add_sample_plans(repository, coursework_id)` for test databases with real coursework and no plans. Never invoked at app startup. |

Plan writers must retain returned IDs when editing; supplied task lists are complete snapshots for that plan. `tasks=None` preserves children; omitting a saved task from a supplied list deletes it. Plan activation uses `StorePlanData` with the existing plan ID and `active` flag. Dates/times are local, minute-precision `YYYY-MM-DDTHH:MM`. The planning owner validates newly created task data and can use the combined-schedule result to display creation conflicts. Coursework timing fields remain coursework context; they do not implicitly create tasks.

Malformed active saved intervals are shown as errors and block corrections until repaired through the owning plan interface. The schedule screen does not introduce a general plan editor.

## Actual results and requirement coverage

Sources: [M1 Requirements](../../docs/documents/first-semester/milestone-1/requirement-2026-09-23.pdf) and [M1 Test Plan](../../docs/documents/first-semester/milestone-1/test.pdf). Only M2 scheduling portions were executed.

| Case / requirement | Actual result and limits |
| --- | --- |
| C7; F33–35, F40–41, I10 | **PASS** for the implemented schedule/storage path. Same-name A1/B1 retain separate IDs/associations; A1 changes, A2 deletion, inactive plans, plan rename/deletion, and restart preserve B1. Automated tests and real browser checks; plan creation/deletion use the repository fixture, not a plan-editor screen. |
| C8; F36–38, I11 | **PASS** for overlap logic, saved-overlap display, and correction. All seven specified intervals tested within/across plans, plus different dates and overnight boundaries. Every affected task has indicators and descriptive warnings. Task-creation notification in the missing planning screen remains unverified. |
| C9; F39 | **PASS**. A1 10–11, B1 11–12, A2 10:30–11:30 identify both overlaps. Student correction of A2 to 12–13 clears them and persists. |
| N3 M2 schedule; F8–10 | **PASS**. Monday/Tuesday daily and weekly views; move A1 to 9–10; reject 11:30–12:30 and retain 9–10. Completion/rewards/reminders portions excluded. |
| C13 M2; P5–6 | **PASS** for correction and conflict-display timings below, three trials each. Creation/deletion screen timings and full planning/export workflow remain unverified. |
| Transactions / restart | **PASS**. Update/delete statement failures and deferred commit failure retain prior snapshots. Actual Streamlit process termination/relaunch restores latest IDs, corrected times, deleted A2, and unchanged B1. Foreign-key check returns no violations. |

[Application test log](application-tests.txt): **64 passed in 0.81 seconds**, including 30 new schedule/service cases and three new Streamlit AppTest cases. [M1/demo regression log](demo-tests.txt): **76 passed in 0.17 seconds**. Total: **140 passing tests**.

The [browser result](browser-results.json) is **PASS**, recorded at 21:49:41 America/New_York on October 25. Environment: macOS 26.6.2 arm64, Python 3.11.11, SQLite 3.53.4, Streamlit 1.49.1, Playwright 1.64.0, Chromium 156.0.8078.4. Source hashes and the base commit are recorded there. Browser tests use a disposable database with two coursework records, two fixture plans, four tasks, and one feedback record; initial/final database size is 40,960 bytes.

Timings use `perf_counter` immediately before the actual button click through assertions that the result is rendered, with the app already started. They do not measure cold startup or large datasets.

| Trial | Accepted correction → schedule / confirmation | Rejected correction → conflict details |
| --- | ---: | ---: |
| 1 | 0.071435 s | 0.082550 s |
| 2 | 0.069191 s | 0.081025 s |
| 3 | 0.066932 s | 0.081776 s |

Every observation is below two seconds. The final browser run also entered coursework manually and through CSV controls, attached sample plans to the real saved coursework, corrected times, restarted the server, and verified activation/deletion refreshes.

Earlier `browser-attempt-*.json` files retain failed automation attempts: date-input accessibility names, hidden radio controls/calendar popup, waiting for task-selection rerender, and single-option selection. The harness was corrected and the complete final run passed. Those failed attempts are not passing application evidence.

## Screenshots and saved state

- [Weekly saved conflicts](01-saved-conflicts.png) and [daily view](02-daily-conflicts.png): distinct IDs, associated course/plan, all affected indicators, and precise conflict explanations.
- [Rejected correction](03-rejected-correction.png): proposed times and both conflicting tasks; database unchanged.
- [Resolved conflict](04-resolved.png): explicit saved interval and no remaining conflicts.
- [After actual restart](05-after-restart.png): A1 still at 9–10, A2 absent, B1 unchanged.
- [After plan deletion](06-plan-deleted.png): only Plan B's task remains.
- [Before restart](before-restart.json) and [after restart](after-restart.json) are identical academic snapshots. The local, git-ignored `academic-state.sqlite3` is a backup of the later final state after Plan A deletion; it deliberately differs from the restart snapshots. `server.log` retains the browser-run server output.

## Reproduce

From the repository root, using the Python 3.11 environment described in the main README:

```sh
.venv/bin/python -m pytest tests -v
.venv/bin/python -m playwright install chromium
.venv/bin/python -m scripts.verify_cse23_browser
```

Run the preserved demo suite separately from `demos/` with `../.venv/bin/python -m pytest tests -v`. Browser verification writes fresh evidence to this directory and cleans up its server and temporary working database. To inspect the feature manually:

```sh
.venv/bin/python -m scripts.seed_schedule_fixture /tmp/folio-cse23-review.sqlite3
FOLIO_DATABASE=/tmp/folio-cse23-review.sqlite3 .venv/bin/python -m streamlit run app.py
```

Choose October 26, 2026, select task #2, and save `2026-10-26T12:00`–`2026-10-26T13:00`. Restart against the same path to inspect persistence. The seeder refuses existing destinations.

## Remaining integration and report contribution

**The issue's full entry → plan → save/restart → schedule/conflicts → export/revision checkpoint is not complete.** The user confirmed that all relevant project files are in this `folio` folder. The checkout contains the M1 `demos/demos/planning_demo.py`, `m1-demos/cse8/cse8_demo.py`, and tool-evaluation prototypes, but no M2 planning/export/revision screens. The export demo uses hardcoded data and is not a real application workflow. There is no outstanding request to locate another folder.

Once those modules are available, wire their existing plan saves/edits/deletions to the repository contracts above, run the real entry-to-export/revision walkthrough, and capture actual outputs/screenshots and creation/deletion timings. Resolve integration defects with the respective module owners. Fixture-backed checks here must not be described as that full walkthrough.

Caleb's contribution for the M2 report: combined dated schedule logic; full conflict explanations and indicators; student-controlled persisted corrections; transactional plan deletion and locked time updates; real Streamlit schedule wiring; regression tests; browser restart/performance evidence; and documented module contracts. The changes preserve M1 feasibility demos and do not replace another owner's planning/export feature. Screenshots and measured results are ready for the later report/slide task; no slides were created here.
