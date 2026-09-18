# Folio DOCX generation comparison

## Scope and testing method

The DOCX comparison evaluates Python-compatible DOCX generation for a simple Folio document with a title, headings, body text, assignment table, and repeated generation. The comparison evaluates the `python-docx` baseline against `docxtpl`.

## Implementation mechanics

| Candidate | Document model | Template usage | Table support | Formatting control | Maintainability |
|---|---|---|---|---|---|
| `python-docx` | Direct document object model | Direct construction without templates | Good | Good for straightforward documents | High |
| `docxtpl` | Template-based DOCX rendering | Strong | Good | Very good for data-driven templates | Moderate |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| `python-docx` | `python-docx` | `./.venv/bin/python -m pip install python-docx` | 1.2.0 |
| `docxtpl` | `docxtpl` | `./.venv/bin/python -m pip install docxtpl` | 0.20.2 |

## Functional test results

| Checklist item | `python-docx` | `docxtpl` |
|---|:---:|:---:|
| Document creation | Pass | Pass |
| Paragraphs/headings | Pass | Pass |
| Candidate includes a table | Pass | Pass |
| Candidate inserts variable Folio data | Pass | Pass |
| Test reopens document and confirms content | Pass | Pass |
| Repeated generation without errors | Pass | Pass |

## Candidate comparison summary

| Candidate | Implementation simplicity | Template flexibility | Maintainability | Folio fit |
|---|---|---|---|---|
| `python-docx` | Very High | Moderate | High | Very High |
| `docxtpl` | Moderate | High | Moderate | High |

## Version details

- Python: 3.11.x
- python-docx: 1.2.0
- docxtpl: 0.20.2

## Notes on interpretation

Measured observations: both libraries generated the same representative Folio document and retained the expected content after reopening the document. `python-docx` required less effort for direct generation, while `docxtpl` provided more template-oriented reuse.

Engineering judgments: `python-docx` offers the best practical fit for Folio's baseline document-generation need because the library provides a simple, transparent API and supports a straightforward assignment report without requiring a template file.

## Selection: `python-docx`

**Rationale:** The evidence confirms `python-docx` as the baseline candidate. `python-docx` requires less code and offers a simpler, clearer approach than a template-driven alternative for Folio's document-generation requirement while reliably supporting headings, paragraphs, and tables.
