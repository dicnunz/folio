# M3 performance results

All five measured operation variants passed their thresholds on this local fixture. This is not a scalability claim or verification of unavailable creation/deletion editor and plan-save workflows.

| Operation | Runs 1 / 2 / 3 (seconds) | Mean (s) | Maximum (s) | Limit (s) | Result | Raw evidence |
|---|---|---:|---:|---:|---|---|
| Display stored plan | 0.122421 / 0.117210 / 0.116700 | 0.118777 | 0.122421 | ≤ 2 | PASS | browser-cse22/browser-results.json |
| Update displayed schedule (time correction) | 0.065387 / 0.072129 / 0.075089 | 0.070868 | 0.075089 | ≤ 2 | PASS | browser-cse23/browser-results.json |
| Detect/display proposed conflicts | 0.082115 / 0.066965 / 0.077092 | 0.075390 | 0.082115 | ≤ 2 | PASS | browser-cse23/browser-results.json |
| Confirm saved coursework | 0.217020 / 0.079734 / 0.068795 | 0.121850 | 0.217020 | ≤ 2 | PASS | browser-cse22/browser-results.json |
| Validate/import 500 CSV records | 0.132275 / 0.126078 / 0.115587 | 0.124646 | 0.132275 | ≤ 5 | PASS | browser-m3/results.json |

Environment: macOS-26.6.2-arm64-arm-64bit; Python 3.11.11; SQLite 3.53.4; Streamlit 1.49.1; Playwright 1.64.0; headless Chromium 156.0.8078.4. Local HTTP/loopback, no remote backend. Browser viewports: 1440×1100 (CSE22), 1440×1800 (CSE23), 1440×1600 (supplement). Application commit and source hashes are retained in existing browser JSON. Runs occurred November 18, 2026 America/New_York. Package versions are in environment-packages.txt. Machine model/CPU frequency were not captured; OS/architecture are recorded.

## Measurement method and fixtures

`perf_counter` starts immediately before Playwright submits a button click and ends after fresh result visibility assertions. Browser action/wait overhead is included. These are end-user UI measurements, not service-only timers. Database verification occurs after the timing endpoint. No mocked rendering or fabricated timing is used.

- Plan: `seed_academic_fixture`, initially one coursework, two plans/four tasks/two feedback entries, 40,960-byte SQLite. Three coursework saves and one accepted mixed-import row precede plan reads (five coursework records); each plan request begins after page reload. Endpoint: Plan A heading and Entered feedback visible.
- Save confirmation: three distinct coursework names, click Save coursework through visible Coursework saved; each saved row then checked via repository. Same small academic fixture.
- Schedule/conflict: two coursework, two plans/four tasks/one feedback, 40,960-byte SQLite. Overlap recreated via repository before each trial. Conflict measurement: rejected proposed 10:15–11:45 with both affected tasks displayed. Schedule measurement: accepted 12:00–13:00 correction through saved confirmation and No conflicts in this period. The latter is a rendered schedule-result endpoint; it does not measure individual canvas-cell paint timing. Functional table values/indicators are separately checked with AppTest and screenshots. No UI creation/deletion performance was measured because those editors are absent.
- CSV: three files of exactly 500 unique valid rows (`browser-m3/import-500-1.csv` through `-3.csv`). Each trial reloads to clear prior feedback and uploads before timing; endpoint is Accepted: 500; rejected: 0 plus Import processed. Course prefixes differ per run, so no duplicates. Same disposable DB grows from 1 to 501/1001/1501 coursework records; two plans/three tasks/one feedback remain. DB grows from 40,960 to 184,320 bytes. Every trial's 500 persisted records are counted.

Backend-only timing exists in `test_storage_timing_three_runs`; its passing thresholds are not substituted for browser evidence. Tests run with pytest capture; authoritative acceptance timing comes from the retained browser JSON above.

## Reproduction and manual extension

Run the two browser runners from test-summary.md. For unavailable operation variants once implemented: use a new disposable seeded database; record OS/browser/app commit and data size; time from submit/click to visibly updated table or confirmation using browser tracing or timestamped screen recording; repeat three times with fresh distinct data, retain each sample and compute mean/max. For task creation/deletion, ensure the changed row appears/disappears before stopping the timer. For import, upload first, then time Import through accepted/rejected result and verify all 500 rows. Do not use repository-only timers to claim UI performance.
