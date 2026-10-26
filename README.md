# Folio

A senior project at Florida Institute of Technology by **Nicholas Dunzelman and Caleb Brooks**, advised by **Dr. David Luginbuhl**.

Folio is a student academic planning app in development. It is intended to help students turn coursework into manageable tasks, combine tasks from multiple plans into one schedule, and follow through with optional task-completion rewards.

## Current status

The M2 local Streamlit application persists coursework, plans, tasks, and entered feedback in SQLite. Coursework controls use the CSE-20 validation service. The combined daily/weekly schedule shows active-plan tasks, explains conflicts, and lets the student save corrected times. Plan creation/editing and the full planning/export workflow remain under development; explicit fixtures exercise their storage interfaces. The original M1 demos remain runnable.

- [Project website](https://dicnunz.github.io/folio/)
- [Project plan](docs/documents/first-semester/project-plan/project-plan-2026-08-30.pdf)
- [Plan presentation](docs/documents/first-semester/project-plan/plan-presentation-1.pdf)

## Run the local M2 application (Python 3.11)

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m streamlit run app.py
```

The default database is `data/academic.sqlite3`. Set `FOLIO_DATABASE` to use a different database. Startup restores existing records.

For a disposable plan/task/feedback demonstration, choose a new temporary path:

```sh
.venv/bin/python -m scripts.seed_academic_fixture /tmp/folio-review.sqlite3
FOLIO_DATABASE=/tmp/folio-review.sqlite3 .venv/bin/python -m streamlit run app.py
```

Add/edit coursework, import CSV, and open a saved plan. Stop and restart the server with the same database path to verify restoration. The fixture command refuses an existing destination.

Run the application tests from the repository root with `.venv/bin/python -m pytest tests -v`. Run the preserved demo suite separately from `demos/` with `../.venv/bin/python -m pytest tests -v` (the M1 suite uses `src` import layout).

See [CSE-22 implementation, test evidence, and remaining integration](evidence/cse-22/README.md) for interfaces, screenshots, measured timings, rollback coverage, and the M2 contribution handoff.

## Combined schedule and conflict correction

The **Combined schedule** screen reads saved tasks from active plans. Choose Daily or Weekly and a date (weeks run Monday–Sunday). Every row retains its task ID, course, plan, plan ID, and full time interval. Conflict indicators identify the other task IDs, and each warning spells out both tasks and their overlap. Touching endpoints do not conflict; overnight tasks appear on each day they intersect.

Select **Task to correct**, enter local `YYYY-MM-DDTHH:MM` start/end values, and choose **Save corrected times**. Invalid or conflicting corrections leave the saved interval unchanged. The app reloads saved plan changes on each interaction; **Refresh schedule** also picks up edits from another session. Inactive/deleted plans and removed tasks disappear from the combined schedule.

To review a disposable example with two overlapping plans:

```sh
.venv/bin/python -m scripts.seed_schedule_fixture /tmp/folio-schedule-review.sqlite3
FOLIO_DATABASE=/tmp/folio-schedule-review.sqlite3 .venv/bin/python -m streamlit run app.py
```

Choose October 26, 2026. Task #2 overlaps tasks #1 and #4. Correct task #2 to `2026-10-26T12:00`–`2026-10-26T13:00`, then restart using the same database to verify it remains saved. The fixture command refuses existing files and is never run at application startup.

See [CSE-23 implementation and actual evidence](evidence/cse-23/README.md) for tests, screenshots, timings, module handoff, and the unavailable full planning/export/revision integration checkpoint. Coursework CSV intervals remain context; they do not automatically create plan tasks.

## Coursework CSV format

Required headers: `course,item_name,due_date`. Optional headers: `score,start_time,end_time`.
Dates use `YYYY-MM-DD`. Start/end times use `YYYY-MM-DDTHH:MM` (24-hour local time, no timezone suffix or seconds). Supply both times or leave both blank; the end must be later than the start. Dates in the time fields allow overnight intervals. The interval is independent of the due date.

```csv
course,item_name,due_date,score,start_time,end_time
CS 491,Design Review,2026-10-26,,2026-10-26T09:00,2026-10-26T10:30
MATH 240,Homework 5,2026-10-28,92,,
```

Use [examples/coursework-with-times.csv](examples/coursework-with-times.csv) to try an import. Manual creation and editing expose the same optional fields. Existing CSVs without times remain valid. Duplicate detection still uses course, assignment name, and due date; changing only a time does not make a new record. These fields retain coursework timing context and do not automatically create or reschedule plan tasks.

Version 1 application databases automatically upgrade to version 2 on startup to add these fields. The upgrade is transactional and preserves records, IDs, and plan/task relationships. The demo CSV adapter also adds nullable time columns so it retains imported intervals.

## Planned functionality

- Manual and CSV entry of course schedules, assessments, deadlines, and scores.
- Editable planning templates and daily or weekly scheduling across active plans.
- PDF and DOCX plan exports, with instructor emails prepared for student review.
- Task completion, progress tracking, configurable reminders, and optional games and rewards.

Students control their plans and choose what to share with an instructor. Planning remains usable without the game or rewards.

## Technical direction

The project plan proposes Python and Streamlit, Pandas for course data, SQLite for storage, and Playwright and python-docx for exports. Tool selection and small technical demos are part of Milestone 1.

## Repository

`docs/` contains the course website and submitted documents. GitHub Pages publishes from that folder. To preview the website locally:

```bash
python3 -m http.server 8000 --directory docs
```

Open <http://localhost:8000>. This serves the course website, not the planned application.
