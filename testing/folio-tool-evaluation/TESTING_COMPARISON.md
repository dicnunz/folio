# Folio automated and browser testing comparison

## Scope and testing method

The testing comparison focuses on automated UI testing and browser-driven validation for the existing Streamlit prototype. The comparison deliberately excludes unrelated production deployment concerns and uses the repository's existing Folio assignment flow.

The comparison covers these candidates:

- Playwright
- Selenium
- Streamlit AppTest (where appropriate)

## Implementation mechanics

| Candidate | Execution model | UI realism | Streamlit compatibility | Debugging experience | CI suitability |
|---|---|---|---|---|---|
| Playwright | Real browser automation | Very high | Good with browser-driven app execution | Excellent | Very high |
| Selenium | Real browser automation | Very high | Good when a server deploys or serves the app | Good | High |
| Streamlit AppTest | In-process testing of Streamlit app objects | Medium | Very high | Good | High |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| Playwright | `playwright` | `./.venv/bin/python -m pip install playwright` | 1.62.0 |
| Selenium | `selenium` | `./.venv/bin/python -m pip install selenium` | 4.49.0 |
| Streamlit AppTest | `streamlit` (already installed) | `./.venv/bin/python -m pip install -r streamlit-requirements.txt` | 1.49.1 |

## Functional test results

| Checklist item | Playwright | Selenium | AppTest |
|---|:---:|:---:|:---:|
| Application loads | Pass | Pass | Pass |
| Assignment field available | Pass | Pass | Pass |
| User can enter a due date | Pass | Pass | Pass |
| User can select a priority | Pass | Pass | Pass |
| User can add an assignment | Pass | Pass | Pass |
| Result appears | Pass | Pass | Pass |
| Multiple assignments remain | Pass | Pass | Pass |
| Tool rejects a blank assignment | Pass | Pass | Pass |
| No normal-use crash | Pass | Pass | Pass |

## Candidate comparison summary

| Candidate | Setup complexity | Browser realism | Reliability | Debuggability | Folio fit |
|---|---|---|---|---|---|
| Playwright | Moderate | Very High | High | High | Very High |
| Selenium | Moderate | Very High | High | Moderate | High |
| AppTest | Low | Medium | High | High | High for Streamlit logic |

## Version details

- Python: 3.11.x
- streamlit: 1.49.1
- playwright: 1.62.0
- selenium: 4.49.0

## Notes on interpretation

Measured observations: Playwright and Selenium both exercised the same browser behavior successfully, while AppTest required less setup for direct Streamlit application-logic validation. The browser-based tools approximate end-to-end UI testing more closely, while AppTest offers a lighter Streamlit-internal testing approach.

Engineering judgments: Playwright offers Folio the strongest practical UI testing choice because Playwright aligns well with real browser execution and supports CI use. AppTest provides value through fast Streamlit-only checks, but AppTest does not provide a full browser-driven test of the actual UI layer.

## Selection: Playwright

**Rationale:** The evidence confirms Playwright as Folio's baseline browser-testing choice. Playwright exercises the actual browser interface, provides strong debugging capabilities, and offers the most appropriate option for future automated UI validation in CI.
