# M3 evaluation evidence

On November 18, 2026, the Folio checkout at `6a6c3cc94cf6e6d4fdb91fd9098ab98c2218c6e5` passed all **140 existing automated tests** (64 application, 76 demo). Three supplemental regression assertions produced **2 passes and 1 failure**. No automated cases were skipped. The failure demonstrates that scheduling a linked preparation task after its coursework due date is accepted and persisted. Overall M3 acceptance is therefore **not achieved**.

Real Chromium/Streamlit sessions with disposable SQLite data verified schedule conflicts and correction, touching and overnight intervals, academic restoration after stopping/restarting the actual server, task/plan removal reflected after refresh, invalid-input rejection, write-failure rollback and preservation of a newer record on stale submission. Fixture-assisted plan/task setup and deletion must be disclosed. Completion flags are tested in storage; completion UI, plan progress, reminders and connected persistent rewards are unavailable and are not passing results.

Three measured trials of each supported UI operation met the requested thresholds. Maximum observed durations: Display stored plan: 0.122s; Update displayed schedule (time correction): 0.075s; Detect/display proposed conflicts: 0.082s; Confirm saved coursework: 0.217s; Validate/import 500 CSV records: 0.132s. Limits were 2 seconds for plan display/schedule update/conflicts/save confirmation and 5 seconds for CSV import. These are local fixture measurements; unavailable editor variants and large schedule scaling were not measured.

Use in the report/presentation:

- Test totals and failure: application.xml, demos.xml, m3-regressions.xml and matching logs.
- Conflict resolution: browser-cse23/01-saved-conflicts.png, 03-rejected-correction.png, 04-resolved.png.
- Real restart evidence: browser-cse23/05-after-restart.png plus before/after-restart.json; browser-cse22 equivalents.
- Deadline defect: browser-m3/deadline-accepted.png and deadline-before/after.json.
- Edge cases/rollback: browser-m3/touching.png, overnight-next-day.png, write-failure.png, stale-update.png.
- Timings: performance-results.md and original browser-results.json/results.json; 500-row fixtures and import screenshot are retained.
- Scope and unavailable cases: acceptance-matrix.md and functional-results.md. Do not present all M3 requirements as complete or demo rewards as connected app acceptance.

All changes are testing/reporting artifacts under tests/results/m3/. Production source and production data were not modified. Historical evidence was preserved.
