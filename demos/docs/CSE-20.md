# CSE-20 implementation and review notes

Status: service implementation and prototype SQLite integration are tested. CSE-20 is **not complete at application level**: the CSE-19 coursework UI, CSE-22 production repository, and coursework-to-plan integration are absent from this checkout. No commits, pushes, PRs, slides, or production-data changes were made.

## Sources and scope

Reviewed the supplied Folio Design Document (sections 3.1, 4.1–4.2, 5.1, 5.6), supplied Folio Requirements, repository `docs/documents/first-semester/milestone-1/requirement-2026-09-23.pdf`, and repository `test.pdf`. The supplied requirements stop at F52; the newer repository requirements include F53 and F54. These require schedules, assessments, deadlines, and scores as planning context. Neither the documents nor the current coursework model specifies separate schedule/assessment fields and formats. Those schemas need agreement before implementing them; unsupported fields are rejected explicitly rather than silently lost.

The data dictionary defines course, assignment name, due date, and an optional score. The existing prototype calls assignment name `item_name`; this API retains that spelling. Scheduled `Task` contains `plan_id`, but no coursework identifier, and there is no academic-plan repository. The existing `tinyfolio.py` uses session-state dictionaries with Assignment, Due Date, and Priority; it has neither course controls nor CSV import, editing, deletion, or service calls. Replacing those controls would be CSE-19 work.

## Files

| File | Change |
| --- | --- |
| `demos/src/coursework.py` | New domain validation, parsing, physical row locations, and set-based deduplication. No SQLite or Streamlit imports. |
| `demos/src/coursework_service.py` | New creation/edit/deletion/import orchestration and documented repository transaction contract. |
| `demos/src/csv_storage.py` | Reuses existing insert/read/database helpers through a SQLite adapter; legacy functions delegate to shared rules. New databases allow an omitted score. |
| `demos/tests/test_coursework_service.py` | 36 collected checks, including parametrized validation, real SQLite failure injection, commit rollback, and three performance runs. |
| `demos/docs/CSE-20.md` | Review, API, decisions, integration instructions, coverage, and manual checks. |
| `demos/docs/CSE-20-test-results.txt` | Actual verbose Python 3.11 test output with each test's status and benchmark measurements. |

The pre-existing untracked `.vscode/settings.json` came from the earlier interpreter fix, not this feature. Existing tests and UI code were not modified.

## Functions and contracts

Results are dictionaries to retain the prototype's conventions; there is no Streamlit dependency.

| Function | Parameters | Return / behavior |
| --- | --- | --- |
| `normalize_row` | field dictionary | New dictionary with trimmed strings, date objects converted to ISO strings, numeric scores converted to floats, missing/blank score converted to None. Does not mutate input. |
| `validate_coursework` | field dictionary | `{record, errors}`. All errors have `field`, `code`, `message`. Required/type/date/score/unsupported-field checks; no saving. |
| `parse_csv` | path or readable text/binary stream, optional source label | `{rows, file_errors, source}`. Each row has `record`, physical `row_number`, `end_row_number`, and `source`. A file error returns no rows. |
| `duplicate_key` | validated normalized record | Tuple `(course, item_name, due_date)`. |
| `validate_and_deduplicate` | parsed row envelopes, optional existing keys | `{accepted, rejected}` lists. Rejections retain locations, source, structured `field_errors`, and compatibility message list `errors`. No persistence. |
| `CourseworkService(repository)` | repository adapter | Service bound to storage. See transaction contract below. |
| `create_coursework` | coursework_data dictionary | `{success, record, errors}`; normalized saved record includes ID/source. Invalid or duplicate records are not saved. |
| `edit_coursework` | coursework_id, changes dictionary | Same result. Retrieves original, validates a merged copy, preserves ID/source, saves only after validation. Not-found and storage errors are structured. Attempts to change ID/source are rejected. |
| `delete_coursework` | coursework_id | Same result; on success `record` is the deleted record. Returns not_found, relationships_unknown, dependent_records, or storage errors without deletion. |
| `import_coursework_csv` | CSV path/stream, optional source label | Import summary described below; parsing completes before opening a write transaction. |
| `SQLiteCourseworkRepository` | database_path, optional dependency_checker | Prototype adapter; transaction creates the existing table if absent and commits or rolls back all changes. |
| `read_csv` | CSV path/stream | Legacy list-of-dictionaries return. File errors still raise ValueError. |
| `validate_row` | field dictionary | Legacy list of error messages using the shared validator. |
| `is_duplicate` | SQLite connection, normalized row | Boolean using the three required fields. |
| `insert_row` | SQLite connection, validated row, source | Existing low-level insert returns ID; callers must validate and own the transaction. |
| `import_csv` | csv_path, database_path | Existing entry point delegates to the service. File failures now produce structured results instead of escaping exceptions. |
| `get_all_records` | database_path | Existing ordered list of stored dictionaries, suitable for a future coursework selector. Storage failures still raise at this low level. |

`csv_storage.REQUIRED_COLUMNS` retains the original four-column writer list so existing fixtures and demos that include score keep working. New UI code must use `coursework.REQUIRED_COLUMNS` (or `csv_storage.COURSEWORK_REQUIRED_COLUMNS`) for the actual three required fields. `coursework.OPTIONAL_COLUMNS` contains score.

## Validation and CSV decisions

Course/item names are trimmed, case-sensitive nonblank text. Dates must be real calendar dates spelled exactly YYYY-MM-DD; Python `date` objects are also accepted for manual controls. Compact and ISO week dates are rejected even though Python can parse some of them. Score is optional and finite numeric when supplied; there is no invented 0–100 limit. Booleans are not scores. No gamification flag gates score storage.

CSV uses the standard library with strict parsing and UTF-8/BOM support. Headers use exact existing field names. Duplicate, blank, unsupported, and missing-required headers are file errors. Extra row values are row errors; absent required values are reported by validation. Quoted commas/newlines work; blank physical lines are ignored. Row numbers refer to physical starting lines, including blank lines; the ending line is also retained. Empty input is a missing-columns file error; a valid header-only file succeeds with zero records. Caller streams remain open and are consumed from their current position.

A parser/file error discards the entire parsed prefix before storage is accessed. Invalid individual rows do not stop valid rows from importing. Source filenames/labels are retained in parsed and rejected entries and the import summary; persisted provenance stays `manual`/`csv` for compatibility. Per-record filenames are not added to the database schema.

Duplicate keys use the three normalized required fields, **excluding optional score**. Distinct scores for the same coursework do not create separate imported records. Duplicate comparison remains case-sensitive. Existing records are checked too, preserving the prototype's cross-import rejection behavior, now consistently using the required fields. Creation/editing use that same rule. Requirements only explicitly mandate deduplication within an import; cross-import behavior is an inherited policy to review, not a new claimed requirement. Invalid rows do not reserve a key.

## ImportResult dictionary and counts

- `total_rows`: parsed data rows, excluding blank lines/header.
- `inserted_rows` and `accepted_count`: records actually committed (equal).
- `invalid_rows`: rejected rows with validation errors.
- `duplicate_rows`: otherwise-valid duplicate rows; each counts once.
- `rejected_count`: all records not saved. Normally invalid_rows + duplicate_rows.
- `errors`: one row envelope for each rejection, including all field errors.
- `file_errors`: parsing/header/read errors. No records are saved; total/counts are zero because no complete parsed file is accepted.
- `storage_errors`: failed transaction messages. All valid candidate writes roll back; accepted count is zero, rejected count equals total_rows. Previously valid candidates receive row-level storage errors. In this case rejected_count also includes storage rejections, not just invalid/duplicate counts.
- `records`: successfully committed records, empty after rollback.
- `source`: source filename or caller label.
- `success`: the complete file was processed and the transaction committed. It may be true with rejected rows, including an entirely invalid file; inspect counts and errors. False means file/storage failure.

## Storage and deletion

The service uses a small adapter contract because CSE-22 has no concrete repository in this checkout. `repository.transaction()` yields methods `list_records()`, `get(id)`, `insert(record, source)`, `update(id, record)`, `dependencies(id)`, and `delete(id)`. Insert/update return saved dictionaries. Repository errors must be raised as `RepositoryError`, and any exception leaving the context must roll back. The service only reports success after context exit/commit. Programmer exceptions are not swallowed.

The SQLite adapter reuses the original table and insert helper. `BEGIN IMMEDIATE` protects duplicate checking and writes in one transaction; foreign-key enforcement is enabled. No new plan/task tables or production schema are invented. Its legacy four-column unique constraint remains; the service enforces three-field uniqueness. Direct low-level callers bypass service validation/duplicate policy and must not be used by the new UI.

**Legacy database limitation:** new prototype databases have nullable score. Existing databases with `score NOT NULL` are not rebuilt or silently migrated; score-less writes return storage errors and preserve data. CSE-22 must supply a reviewed nullable-score migration that preserves IDs, indexes, and foreign keys. Existing duplicates with different scores are not cleaned up automatically.

**Deletion policy decision:** the design says check relationships but supplies no cascade, detach, or archive rule. Default deletion refuses when relationships cannot be checked. The injected `dependency_checker(connection, id)` must inspect actual plan/task associations in the same transaction and return an empty collection only when none exist. References block deletion. Foreign keys provide another guard. Tests explicitly supply an empty checker only for databases with no relationships. Never wire an always-empty checker into a real application. The final policy and production relationship queries remain CSE-22 dependencies.

## CSE-19 / planning handoff

From the existing demos import layout:

```python
from src.coursework_service import CourseworkService
from src.csv_storage import SQLiteCourseworkRepository
from src.coursework import REQUIRED_COLUMNS, OPTIONAL_COLUMNS

service = CourseworkService(SQLiteCourseworkRepository(database_path))
result = service.create_coursework({
    "course": course, "item_name": assignment_name,
    "due_date": due_date, "score": score_or_none,
})
import_result = service.import_coursework_csv(uploaded_file, source=uploaded_file.name)
edit_result = service.edit_coursework(coursework_id, changes)
delete_result = service.delete_coursework(coursework_id)
```

Use the real CSE-22 adapter when available. Show each service error's field/message and every rejected row's source/location/field_errors. Show accepted_count/rejected_count, file_errors, and storage_errors. Display required column names and YYYY-MM-DD instructions before import. Rewind a reused upload before another import. Refresh the coursework selector after successful writes, preserving returned IDs for plan links. The repository `list_records()` supplies the planning context, but no existing plan selector can be connected yet. Do not copy records into unrelated session state as a substitute for persistence.

## Executed verification (2026-10-19)

Command from `demos/`:

```sh
PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/python3.11 -m pytest -v -s
```

76 tests passed in 0.13 seconds: all 40 pre-existing demo tests plus 36 new collected checks. The adjacent test-results file lists every test name, parametrized case, and PASS status. No tests failed in either implementation suite run. The final run followed connection-lifetime cleanup and addition of a deferred-constraint commit-failure test.

Coverage includes valid create/edit/delete/reopen; independent and combined required-field errors; impossible/noncanonical dates; invalid/nonfinite scores; IDs/source immutability; missing identifiers; valid, all-invalid, mixed, empty/header-only, unreadable, malformed, extra-column, BOM, multiline CSV; duplicate groups and cross-import duplicates; missing/unknown/dependent relationship checks; real foreign-key integrity; INSERT/UPDATE/DELETE trigger failures; import-prefix rollback; and deferred-constraint failure at commit. All tests use temporary SQLite files.

P7 service benchmark (three fresh databases, 500 distinct records with numeric scores, fixture generation outside timer):

| Run | Seconds | Accepted | Rejected | Final DB bytes |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.004369 | 500 | 0 | 65536 |
| 2 | 0.004040 | 500 | 0 | 65536 |
| 3 | 0.003752 | 500 | 0 | 65536 |

Environment: macOS 26.6.2 arm64, Python 3.11.11, SQLite 3.53.4, local uncommitted CSE-20 implementation. Timing uses perf_counter around the entire import service call, including parsing, validation, duplicate lookup, database initialization, writes, and commit. Initial DB size is zero/nonexistent. Browser: not applicable to this service measurement. Exact source is the local diff plus accompanying files.

The original csv_sqlite_demo also ran successfully: 4 rows, 2 inserted, 1 invalid, 1 duplicate. Streamlit AppTest executed the unchanged tinyfolio.py: startup, blank-name rejection, and valid assignment creation passed with isolated session state. This additional smoke test used the available Python **3.12** virtual environment and Streamlit 1.49.1; Python 3.11 has no Streamlit installed. It is not CSE-20 UI verification or a browser screenshot. Runtime emitted sandbox CPU-cache lookup warnings but assertions passed.

## Requirements / acceptance status

| Requirement / case | Status and evidence |
| --- | --- |
| F18–19, F21–23 | Implemented and verified at service/prototype storage level: C1 create/edit and C2 parametrized checks. Application controls/display remain CSE-19. |
| F20 | Partial: deletion verified with explicit no-dependency checker; missing/linked/unknown relationships safely refused. Final relationship policy/adapter pending. |
| F24–30 | Implemented and verified at service/prototype storage level by C3–C5 checks. Full displayed interface acceptance pending. |
| F53–54 | Partial: named assessments/deadlines via item_name/due_date and optional scores supported without gamification coupling. Distinct course-schedule schema and context UI unspecified/unimplemented; no full coverage claim. |
| C1 | Service subset verified. Course-schedule entry, UI labels/date guidance, planning context and game-disabled UI checks blocked. |
| C2 | Service behavior verified. UI error presentation not verified. |
| C3 | Service subset: three valid records including quoted comma and optional scores verified. Separate schedule fixtures and import guidance/game-disabled UI blocked. |
| C4 | Five-record fixture (three valid/two invalid, including multiple errors) verified in storage/results. Display checks pending. |
| C5 | File failures, empty/header-only files, duplicates and counts verified. UI display pending. |
| C13 / P7 | Three service timings below five seconds including persistence. Full submitted-action-to-visible-result measurement and seeded plan/task environment NOT verified; requires final app. No M3 timing tests executed. |
| I7–9, I12–14 | Result interfaces ready; UI requirements not implemented by this change. |
| CSE-22 production integration | Blocked: no real repository/relationship schema in checkout. Prototype adapter only. |

## Manual review and follow-up

1. Review the optional-score rule, case-sensitive three-field duplicate key, cross-import policy, unknown-column rejection, and compatibility constant naming.
2. Inspect the transaction context and commit-failure tests. Agree on the legacy score migration with CSE-22 before using old databases with score-less records.
3. Agree on schedule/assessment context formats for F53–54 and a dependent-record deletion policy; supply actual relationship queries. Confirm invalid changes never mutate original records.
4. Run the pytest command above and inspect the new test file alongside actual verbose results.
5. For the existing UI smoke check only, from repository root run `testing/folio-tool-evaluation/.venv/bin/python -m streamlit run testing/folio-tool-evaluation/tinyfolio.py`. Open the printed local URL, click Add Assignment with a blank name (expect the required-name error), then enter a name and add it (expect success and a table row). This prototype has no CSV controls; it cannot verify this service yet.
6. After CSE-19/CSE-22 integration, use a temporary DB: enter blank course/name and an invalid date together (expect all errors/no writes), correct them (expect one saved record), edit invalidly (expect original retained), import the C4 fixture (expect 3 accepted/2 rejected at lines 5/6), repeat a valid import (expect duplicates), and attempt deletion of referenced coursework (expect refusal). Reopen the app to verify saved values and planning links.
7. Repeat the 500-row CSV through the actual UI three times with fresh temporary databases, recording browser, machine, DB size, and submission-to-visible-result times. Only then assess full C13/P7 acceptance.
