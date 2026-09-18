# Folio PDF generation comparison

## Scope and testing method

The PDF comparison evaluates small, Python-compatible PDF-generation approaches for a Folio weekly report. The comparison limits the scope to a simple document with a title, student and project text, multiple assignment rows, and repeated generation.

## Implementation mechanics

| Candidate | Rendering model | Layout control | Text/data handling | Repeated generation | Maintainability |
|---|---|---|---|---|---|
| ReportLab | Direct canvas drawing API | Good for explicit layout control | Straightforward | Reliable | High |
| fpdf2 | Simple cell-based API | Good, but less flexible than canvas APIs | Straightforward | Reliable | High |
| Browser-based HTML-to-PDF | A browser renders the HTML/CSS layout | Very strong | Good when Folio already provides HTML | Usually reliable but depends on browser automation | Moderate |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| ReportLab | `reportlab` | `./.venv/bin/python -m pip install reportlab` | 5.0.1 |
| fpdf2 | `fpdf2` | `./.venv/bin/python -m pip install fpdf2` | 2.8.8 |
| Browser HTML-to-PDF | `playwright` (already installed) | `./.venv/bin/python -m pip install playwright` | 1.62.0 |

## Functional test results

| Checklist item | ReportLab | fpdf2 | Browser HTML-to-PDF |
|---|:---:|:---:|:---:|
| Candidate creates PDF successfully | Pass | Pass | Pass |
| Candidate creates a non-empty file | Pass | Pass | Pass |
| Expected text/data appear | Pass | Pass | Pass |
| Multiple rows render | Pass | Pass | Pass |
| Layout acceptable for simple report | Pass | Pass | Pass |
| Repeated generation succeeds | Pass | Pass | Pass |

## Candidate comparison summary

| Candidate | Implementation simplicity | Formatting control | Maintainability | Folio fit |
|---|---|---|---|---|
| ReportLab | Moderate | High | High | High |
| fpdf2 | Low | Moderate | High | High |
| Browser HTML-to-PDF | Moderate | Very High | Moderate | Moderate |

## Version details

- Python: 3.11.x
- reportlab: 5.0.1
- fpdf2: 2.8.8
- playwright: 1.62.0

## Notes on interpretation

Measured observations: both ReportLab and fpdf2 successfully created non-empty PDFs containing the expected report content and multiple rows. Browser-based HTML-to-PDF can produce excellent formatting, but browser-based conversion requires more runtime and automation complexity for a simple document.

Engineering judgments: fpdf2 offers the cleanest fit when Folio only needs a simple generated report; ReportLab offers a stronger choice when Folio requires more precise layouts or sophisticated PDFs. Browser-driven HTML-to-PDF adds value when Folio already renders HTML in the app, but the baseline requirement does not need browser-driven PDF generation.

## Selection: fpdf2

**Rationale:** The evidence confirms fpdf2 as the practical default for Folio's simple report-generation needs. fpdf2 provides a lightweight, accessible API, generates reports reliably, and supports a small assignment report without introducing browser automation overhead.
