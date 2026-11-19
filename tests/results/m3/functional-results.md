# M3 functional results

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
| S-touching | PASS | Task 1 ends at 11:00; task 4 starts at 11:00; UI reports no conflicts. | browser-m3/results.json |
| E-invalid | PASS | Invalid start rejected visibly; entire saved snapshot compared. | browser-m3/results.json |
| D-deadline-rejection | FAIL | UI accepted and persisted task 1 on November 2, after associated coursework due October 30. No deadline validation feedback. | browser-m3/results.json |
| D-unrelated | PASS | All unrelated task records unchanged after late save. | browser-m3/results.json |
| D-valid-correction | PASS | Valid pre-deadline overnight correction saved. | browser-m3/results.json |
| S-overnight | PASS | Overnight task saved through UI and available in next day schedule selector. | browser-m3/results.json |
| E-write-failure | PASS | Actual SQLite trigger rejected write; UI storage error visible; saved snapshot unchanged. | browser-m3/results.json |
| E-stale-preservation | PASS | External fixture update preserved when stale browser form submitted; UI reset to latest saved interval. | browser-m3/results.json |
| P-import-500 | PASS | Three real UI imports accepted 500 distinct rows each; persisted counts checked. | browser-m3/results.json |
| E-integrity | PASS | SQLite integrity and foreign-key checks passed. | browser-m3/results.json |

Creation of assessments/preparation tasks is represented by coursework due_date and linked plan tasks; there is no explicit preparation-task type or separate assessment-deadline relation. The deadline test uses a date beyond the entire due day, avoiding same-day cutoff ambiguity. Reminder and completion workflows cannot be evaluated by modifying storage fields alone.
