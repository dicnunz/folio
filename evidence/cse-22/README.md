# CSE-22 — academic persistence and application integration

Implemented and verified on **October 21, 2026**, after the assigned October 19 implementation date. This is actual execution evidence, not a backdated deadline claim. Branch: `cbrooks2022/cse-22-m2-persist-academic-data-and-connect-the-application`. No commits, pushes, Linear messages, or presentation slides were made in this task.

## Delivered

- Versioned local SQLite schema for coursework, plans, tasks, and entered feedback.
- Stable generated IDs, enforced foreign keys, restricted coursework deletion, and atomic plan/task/feedback saves.
- `StoreCoursework`, `StorePlanData`, and academic-only `RestoreSavedApplicationState` interfaces.
- CSE-20 coursework service connected to the real repository and local Streamlit app, with manual creation/edit/deletion and CSV import.
- Startup restores the saved academic state on each run; it does not seed or append samples. Each explicit restoration is a consistent read transaction.
- A read-only saved-plan/task/feedback viewer for testing current persistence. Plan editors, templates, revision rules, exports, and daily/weekly schedule screens remain with their owners.
- Disposable plan/task/feedback fixtures and automated repository, app, restart, and browser verification.

The checkout contained no M2 application or CSE-19 screens, only the M1 `tinyfolio.py` feasibility app. `app.py` is now the local M2 entry point. Minimal coursework wiring in `folio/coursework_ui.py` provides the required real controls without modifying the original demos or pretending the missing planning workflow exists. It can be replaced by CSE-19 screens using the same services. CSE-23 still owns the final entry → planning → schedule → export/revision demonstration.

## Files and interfaces

| File | Responsibility |
| --- | --- |
| `app.py` | Streamlit entry point, startup/error handling, saved-plan and associated-task display. |
| `folio/application.py` | `open_application(database_path=None)` creates/initializes the repository and returns `(repository, CourseworkService)`. Explicit path overrides `FOLIO_DATABASE`; default is repository-local `data/academic.sqlite3`. |
| `folio/storage.py` | Schema version 1, SQLite transactions, coursework adapter, plan aggregates, restoration. |
| `folio/coursework_ui.py` | Minimal form/upload/selection wiring to existing CSE-20 validation and structured errors. No SQLite statements or planning rules. |
| `folio/__init__.py` | Application package. |
| `scripts/seed_academic_fixture.py` | Explicit fixture command; refuses existing destination files. Never called by startup. |
| `scripts/verify_cse22_browser.py` | Launches Streamlit and Chromium against a temporary DB; saves screenshots, timings, snapshots, and a SQLite backup. Terminates its server/browser afterward. |
| `tests/test_academic_storage.py` | 15 collected storage/transaction/restoration tests, including parametrized rollback cases. |
| `tests/test_application.py` | Three Streamlit AppTest integration tests. |
| `requirements.txt`, `requirements-dev.txt` | Python 3.11 runtime/test dependencies. NumPy 2 is required for current Arrow wheels. |
| `.gitignore` | Excludes local environments, runtime databases, and generated caches. |
| `README.md` | Local run, fixture and test commands. |
| `evidence/cse-22/*` | Actual execution results and report handoff. SQLite backup is intentionally git-ignored but available locally. |

Existing `demos/` and `testing/folio-tool-evaluation/` source/tests were unchanged. The app reuses the CSE-20 service from `demos.src.coursework_service` rather than copying it. Moving shared services out of the demos tree can be a separate coordinated packaging change.

### Repository contracts

Construct `AcademicRepository(path)` and call `initialize()` once during application startup, or use `open_application(path)`. The repository is not a long-lived connection: each operation opens/closes its own connection. All connections enable foreign-key enforcement.

- `StoreCoursework(action, record)` / `store_coursework`: CREATE returns the saved row with new ID; UPDATE preserves ID/source and rejects missing records; DELETE refuses dependent plans and returns the removed row. Records supplied directly must already be domain-validated. The UI calls `CourseworkService`, not this low-level interface.
- `StorePlanData(plan, tasks=None, feedback=None)` / `store_plan_data`: returns `{plan, tasks, feedback}` after commit. A missing plan ID creates a plan; a supplied ID updates that existing plan. The input plan is a complete snapshot, not a patch. It contains `coursework_id`, `name`, optional `template_id`, `notes`, and `active`. The saved coursework association cannot be silently changed.
- Supplied task/feedback lists are **complete replacements for that plan only**. `None` preserves the existing collection; `[]` deliberately removes all its children. Child rows without IDs create records. Returned IDs must be retained on later saves; existing child IDs must belong to the same plan and appear at most once. Unknown/foreign IDs reject the whole operation. Omitted existing IDs are deleted within the same transaction.
- Task dictionaries contain `id` when saved, `plan_id`, `name`, `start_time`, `end_time`, and `completed`. UI/services should supply validated local ISO date-time strings such as `2026-10-22T10:00`; no timezone conversion is performed. Scheduling conflict and duplicate-task rules remain in scheduling/domain services. The schema guards interval ordering and completion booleans; it is not a substitute for planning validation. Existing M1 `Task.task_id` maps to stored `id` when integrating that class.
- Feedback dictionaries contain `id` when saved, `plan_id`, `suggestion`, optional `decision` (`accept`, `reject`, `adapt`, or None), and `adapted_text`. Recording feedback does not automatically change a plan or tasks. The planning service prepares a student-approved revision, then explicitly saves it.
- `get_plan(id)` returns a saved aggregate or None in a consistent read snapshot.
- `RestoreSavedApplicationState()` / `restore_saved_application_state`: returns `{coursework: [...], plans: [...], tasks: [...], feedback: [...]}`, each ordered by stable ID. It includes all saved plans, including inactive plans. CSE-23 should filter active plans for its combined schedule.
- `transaction()` yields the existing CSE-20 contract: `list_records`, `get`, `insert`, `update`, `dependencies`, `delete`. SQLite failures become `RepositoryError`. The service exposes those as structured storage errors; the app displays startup/restoration errors.

Plan writes use `BEGIN IMMEDIATE`; success returns after commit. Any exception—including a deferred foreign-key failure at commit—closes and rolls back the entire transaction. Related deletes/updates never partially survive. Reads use `BEGIN` so coursework/plans/tasks/feedback come from one snapshot. No `INSERT OR REPLACE` is used, avoiding accidental identity changes.

Foreign keys are coursework ← plan ← task/feedback with ON DELETE RESTRICT. Coursework dependencies are checked by the CSE-20 service and enforced again by SQLite. There is no arbitrary cascade policy. No plan-deletion UI is introduced; deleting a child from a supplied plan snapshot is an explicit operation. Future M3 tables must supply their own reviewed migration and deletion semantics.

### Legacy databases and scope

The new app creates a fresh versioned academic database. It deliberately refuses an unversioned nonempty database or a newer schema version, leaving it unchanged. M1 `records` databases (including their NOT NULL score schema) remain feasibility evidence. A legacy importer/migration is **not implemented**; use a fresh path rather than pointing the new app at a demo DB. Optional scores work in the real CSE-22 schema.

No game/reward/reminder/settings tables or behaviors are implemented here. `completed` is stored/restored as a task fixture field for academic continuity, without executing M3 rewards/progress behavior. No domain rules, export code, or planning template implementation were moved from another team member.

## Executed checks and actual outcomes

Environment: macOS 26.6.2 arm64, Python 3.11.11, SQLite 3.53.4, Streamlit 1.49.1, Playwright 1.64.0, Chromium 156.0.8078.4. `browser-results.json` contains source hashes, base commit, timestamp, sizes, and unrounded timings. `python-environment.txt` records the isolated test environment. The app/database tests use only disposable test paths.

| Check | Actual outcome / evidence |
| --- | --- |
| New repository + Streamlit tests | **18 passed in 0.55s**; each name and status is in `pytest-results.txt`. |
| Preserved CSE-20/M1 demo regression suite | **76 passed in 0.15s**; `demo-regression-results.txt`. Run separately using its original import layout. |
| Real browser validation | Blank manual fields show all three errors; actual screenshot `validation.png`. |
| Real browser creation | Three coursework records saved through controls and verified in SQLite; `coursework-saved.png`. |
| Real CSV upload | Mixed file: one accepted, one invalid, one duplicate; UI shows accepted 1 / rejected 2; `csv-import.png`. |
| Real edit/deletion guard | Changed assignment name saved; deletion of coursework referenced by plans refused. |
| Real saved-plan display | Plan A, its tasks, and entered feedback displayed; `saved-plan.png`. |
| Actual server restart | Terminated Streamlit, saved latest plan/task/feedback fixtures, launched a new process and browser page; updated coursework control and saved-plan notes restored; `restored-after-restart.png`. |
| SQLite state across restart | `before-restart.json` equals `after-restart.json`; 5 coursework, 2 plans, 3 tasks, 2 feedback; foreign_key_check returned no rows. `academic-state.sqlite3` is the real tested DB backup. |
| Rollback | Invalid child/feedback, foreign/repeated child IDs, coursework reassignment, CSV insert failure, and deferred constraint failure at commit preserve prior state. See storage tests. |
| Missing/legacy/newer database | Fresh DB restores empty; legacy/newer DB rejected unchanged; malformed DB produces a visible app error. |
| Dependency validation | `pip check`: no broken requirements found after isolation/fix. |

Initial failures were resolved rather than hidden: the first UI test environment inherited NumPy 1.26 while the installed Arrow wheel required NumPy 2; a fully isolated environment and explicit NumPy constraint resolved it. A cold AppTest dependency import exceeded its default 3-second harness timeout; the harness now allows 15 seconds for startup/execution (this is not a performance acceptance limit). An attempted combined-root run exposed the pre-existing demo `src`/nested `demos` import layout; the suites are run separately without rewriting demo packaging. Final runs above passed. Actual browser timing assertions remain independently fixed at **2 seconds**.

### C13 / P4 and P8 measured browser timings

The fixture database starts at 40,960 bytes with two plans, four tasks, one coursework record, and two feedback records. Browser timing uses `perf_counter` immediately before the actual button click through assertions that the result is visible. The app is already started and its fixture table rendered; these are interactive response times, not cold process-startup benchmarks. The final database is also 40,960 bytes.

| Run | Coursework save → visible confirmation | Open saved plan → plan + feedback visible |
| --- | ---: | ---: |
| 1 | 0.079444 s | 0.102984 s |
| 2 | 0.071129 s | 0.117744 s |
| 3 | 0.068280 s | 0.104728 s |

All six observations passed the 2-second threshold. Each saved coursework record was also checked in SQLite. Plan aggregate repository saves were measured separately at 0.000504, 0.000329, and 0.000328 seconds; plan reads at 0.000110, 0.000107, and 0.000104 seconds. These repository timings do **not** stand in for a missing plan-editor save confirmation UI.

## Requirements / M1 Test Plan mapping

| Requirement/case | Verification status |
| --- | --- |
| F31–32 academic M2 state | Implemented/verified: latest coursework, plans, tasks and entered feedback persist across new repository instances, separate Python processes, and actual Streamlit restart. No duplicates or automatic seeds. M3 categories excluded. |
| F33 | Implemented/verified: IDs/FKs preserved, identical task names across plans remain distinct, foreign child IDs and coursework reassignment rejected, dependent deletion blocked. |
| P1 | Entered/edited plan, task, feedback, and coursework values retained; verified by exact snapshot comparison after restart. |
| P4 | Stored-plan display verified in the browser, three runs under two seconds. |
| P8 | Coursework save/visible confirmation verified, three browser runs under two seconds. Plan/task transaction timings pass, but their screen-level save confirmation awaits Nicholas's actual editing controls. |
| C6, academic subset | Passed storage/process/browser restoration checks and empty database check. Game/reward state and displayed-progress behavior are M3 and not executed. |
| C7, storage subset | Passed: rescheduled A1 preserves ID/plan; removed A2 stays removed; same-named B1 and plan B unchanged after restart. Read-only app view shows plan/course associations. Interactive combined daily/weekly schedule operations remain CSE-23. |
| C13, available M2 subset | Passed P4 + coursework P8 browser checks and plan aggregate repository timings. Full C12 environment/full planning workflows and unavailable screen actions remain for CSE-23. No M3 completion/reminder/game cases claimed. |

## Reproduce and inspect

From repository root, install using Python 3.11 as described in the root README. Then:

```sh
.venv/bin/python -m pytest tests -v -s
# From demos/ in a separate shell:
../.venv/bin/python -m pytest tests -v -s
```

Browser test from repository root:

```sh
.venv/bin/python -m playwright install chromium
.venv/bin/python -m scripts.verify_cse22_browser
```

This starts/stops its own local server and overwrites the generated CSE-22 evidence with the new actual run; it never touches the default application DB. For this recorded execution the environment/browser downloads were under `/tmp/folio-cse22-venv` and `/tmp/folio-cse22-browsers`, with `PLAYWRIGHT_BROWSERS_PATH` set accordingly.

Inspect the saved database locally with SQLite tooling (the backup contains only generated fixture/browser-test records). In SQL, inspect `coursework`, `plans`, `tasks`, `feedback`, and `PRAGMA foreign_key_check`. The JSON snapshots provide the same academic rows in a reviewable text format. To inspect manually without altering the evidence DB, copy it to a temporary file and launch `app.py` using `FOLIO_DATABASE` pointing to that copy.

Manual walkthrough: save valid coursework, attempt an invalid edit, upload mixed CSV, open Plan A, try deleting its linked coursework (expect refusal), then stop/restart Streamlit with the same DB and reopen the plan. Verify IDs and latest values. Plan/task changes are explicitly fixture-driven until the owning screens are available.

## Contribution and remaining handoff

Caleb's CSE-22 contribution: designed and implemented the academic SQLite schema/repositories, atomic writes and consistent restoration; connected CSE-20 manual/CSV services to the local application; implemented the dependency check; preserved the M1 demos; produced automated rollback/restart/browser tests and actual performance/screenshots for the report.

Ready for Nicholas: `open_application`, `StorePlanData`, `get_plan`, and returned IDs let planning screens save a complete student-approved plan/task/feedback aggregate. Preserve IDs, use None to retain untouched child collections, and do not reuse another plan's child IDs. Use restored coursework for selection. No instructor decision is automatically applied by storage.

Remaining for CSE-23: connect real template/task-edit/feedback-revision/export workflows as they arrive; build the active-plan daily/weekly schedule and conflict display; verify the final integrated walkthrough and unavailable screen-level P8 cases. Legacy M1 DB migration and future M3 schema migrations need separate reviewed implementation if required. Do not mark full end-to-end integration complete from these fixture-supported checks alone.

Sources inspected locally: approved project plan (M2 §§1–2), M1 progress evaluation (next-milestone split), published five-page M1 Design (persistence/service interfaces), requirements, and Test Plan C6/C7/C13 under `docs/documents/first-semester/`. No presentation work or external coordination messages were performed.
