# M3 failures, gaps and recommended fixes

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
