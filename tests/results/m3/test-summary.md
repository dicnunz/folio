# M3-11 execution summary

Executed November 18, 2026 (America/New_York), commit `6a6c3cc94cf6e6d4fdb91fd9098ab98c2218c6e5`. This checkout identifies itself as the M2 local app. M3 acceptance is **not complete**: deadline enforcement fails and multiple required workflows are not implemented.

| Suite | Executed | Passed | Failed | Errors | Skipped | JUnit duration | Evidence |
|---|---:|---:|---:|---:|---:|---:|---|
| Existing application | 64 | 64 | 0 | 0 | 0 | 0.751 s | application.xml |
| Existing demos | 76 | 76 | 0 | 0 | 0 | 0.186 s | demos.xml |
| New M3 regression assertions | 3 | 2 | 1 | 0 | 0 | 0.046 s | m3-regressions.xml |

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
