# Folio CSV and data processing comparison

## Scope and testing method

The CSV comparison isolates CSV ingestion, filtering, update, sorting, export, reload, and malformed-input handling for Folio-style assignment records. The comparison excludes UI, database logic, and unrelated analytics features.

The tests used the same representative dataset for each candidate:

- Design Review / CS 491 / High / 2026-09-30 / 10
- Lab 2 / CS 491 / Medium / 2026-10-02 / 5
- Reading / ENG 210 / Low / 2026-10-01 / 2

## Implementation mechanics

| Candidate | Data representation | Filtering/edit mechanics | CSV import/export | Error handling | Integration with Python/Streamlit | Maintainability |
|---|---|---|---|---|---|---|
| Python stdlib `csv` | List of dictionaries | Manual filtering and row mutation with `DictReader` / `DictWriter` | Native CSV parsing and serialization | Explicit checks for missing columns or malformed rows | Very easy to use with Streamlit state or in-memory data | Very high for simple tasks |
| Pandas | DataFrame | Column-based filtering, assignment, and sort operations | `read_csv` and `to_csv` | `NaN`/missing values need explicit handling | Very good for UI-driven data workflows and quick transformations | High |
| Polars | Lazy or eager DataFrame | Expression-based filtering and mutation with `pl.col()` | `read_csv` and `write_csv` | Strong schema and null handling; Polars catches some errors earlier | Very good for Python workflows and columnar transforms | High |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| Python stdlib `csv` | None | None | Python 3.11.x |
| Pandas | `pandas` | `./.venv/bin/python -m pip install pandas` | 2.5.3 |
| Polars | `polars` | `./.venv/bin/python -m pip install polars` | 1.44.2 |

## Functional test results

| Checklist item | `csv` | Pandas | Polars |
|---|:---:|:---:|:---:|
| Load CSV | Pass | Pass | Pass |
| Read assignment records | Pass | Pass | Pass |
| Filter by priority | Pass | Pass | Pass |
| Modify an existing record | Pass | Pass | Pass |
| Add a new record | Pass | Pass | Pass |
| Sort records | Pass | Pass | Pass |
| Export to CSV | Pass | Pass | Pass |
| Reload exported CSV | Pass | Pass | Pass |
| Values remain correct | Pass | Pass | Pass |
| Candidate handles malformed input safely | Pass (manual checks) | Pass (schema-aware checks) | Pass (schema-aware checks) |

## Candidate comparison summary

| Candidate | Data-size fit | Filtering power | Edit complexity | CSV ergonomics | Maintainability | Suitability for Folio |
|---|---|---|---|---|---|---|
| Python stdlib `csv` | Very High | Moderate | Low | Very High | Very High | Very High |
| Pandas | High | Very High | Low | High | High | Very High |
| Polars | High | Very High | Low | High | High | High |

## Version details

- Python: 3.11.x
- pandas: 2.5.3
- polars: 1.44.2

## Notes on interpretation

Measured observations: all three candidates successfully processed the same CSV dataset, filtered records, modified values, added new rows, sorted by date, exported, and reloaded the CSV without data loss.

Engineering judgments: the Python standard library offers the simplest and most maintainable choice for Folio's expected local, application-scale data. Pandas offers an excellent fit when Folio needs more spreadsheet-like transformations. Polars competes strongly with Pandas, but only larger data volumes or expression-heavy transformations would justify the extra dependency for the baseline.

## Selection: Python stdlib `csv`

**Rationale:** The baseline CSV approach supports Folio's small local data workload, adds no dependency cost, and offers the most transparent option for simple assignment-record processing. The evidence confirms the baseline as the most practical fit unless future requirements introduce larger tabular analysis workflows.
