# Folio persistent data storage comparison

## Scope and testing method

The storage comparison isolates small local persistence for Folio assignment records. The comparison does not benchmark database performance or assume a large multi-user workload.

The tests used the same representative records for each candidate:

- A1 / Design Review / CS 491 / High / 2026-09-30
- A2 / Lab 2 / CS 491 / Medium / 2026-10-02

The tests evaluated each candidate for create, read, update, delete, persistence across reopen or restart, filtering, and data-validity checks.

## Implementation mechanics

| Candidate | Schema/model | CRUD mechanics | Query capability | Relational capability | Persistence mechanics | Maintainability |
|---|---|---|---|---|---|---|
| SQLite (`sqlite3`) | Explicit table schema with typed columns | Straightforward SQL statements | Strong, SQL-based filtering and ordering | Good for simple relationships | File-based database on disk | High |
| JSON file storage | Plain dict/list in a file | Manual mutation of Python objects, then `json.dumps` | Simple Python filtering on loaded data | Limited; application code manages relationships | Serialize and deserialize a file | High for small data |
| TinyDB | JSON document database with table-like storage | Insert, update, remove, search | Moderate; TinyDB offers simple query syntax but less query power than SQL | Limited; application code manages relationships | JSON-backed file database | Moderate-High |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| SQLite | Python standard library | None | Python 3.11.x |
| JSON file storage | Python standard library | None | Python 3.11.x |
| TinyDB | `tinydb` | `./.venv/bin/python -m pip install tinydb` | 4.9.0 |

## Functional test results

| Checklist item | SQLite | JSON | TinyDB |
|---|:---:|:---:|:---:|
| Create records | Pass | Pass | Pass |
| Read records | Pass | Pass | Pass |
| Update records | Pass | Pass | Pass |
| Delete records | Pass | Pass | Pass |
| Persist across reopen | Pass | Pass | Pass |
| Filter/query records | Pass | Pass | Pass |
| Maintain unique identifiers | Pass | Pass | Pass |
| Candidate rejects invalid data | Pass (schema enforcement) | Pass (manual validation) | Pass (manual validation) |
| Simple relationship model | Pass (foreign-key-friendly design) | Partial (manual join logic) | Partial (manual join logic) |

## Candidate comparison summary

| Candidate | CRUD simplicity | Query power | Relationship support | Maintainability | Folio fit |
|---|---|---|---|---|---|
| SQLite | High | Very High | High | High | Very High |
| JSON file storage | Moderate | Moderate | Low | High | High |
| TinyDB | High | Moderate-High | Low | Moderate-High | Moderate-High |

## Version details

- Python: 3.11.x
- tinydb: 4.9.0

## Notes on interpretation

Measured observations: all three candidates persisted the same records correctly across reopen/restart, supported CRUD operations, and kept the expected values.

Engineering judgments: SQLite offers the most robust and scalable option for Folio's local assignment data because SQLite provides an explicit schema and reliable query behavior without server overhead. JSON provides a valid lightweight fallback when Folio stores a very small dataset and the project intentionally avoids database complexity. TinyDB works for the use case, but TinyDB adds a layer of abstraction without providing a strong operational benefit over SQLite for a small local app.

## Selection: SQLite (`sqlite3`)

**Rationale:** The evidence confirms SQLite as the practical baseline for Folio. SQLite provides reliable local persistence, an explicit schema, simple query capabilities, and good maintainability without changing the project's small-scale architecture.
