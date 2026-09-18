# Technical tool selection summary

## Technical baseline selections

| Area | Candidates | Selection | Version | Concise Rationale |
|---|---|---|---|---|
| CSV and data processing | Python stdlib `csv`, Pandas, Polars | Python stdlib `csv` | Python 3.11.x | Simplest and most maintainable for small Folio assignment data; no dependency cost and direct data control. |
| Persistent data storage | SQLite, JSON, TinyDB | SQLite | Python 3.11.x + sqlite3 | Best local persistence with explicit schema and reliable queries for a small app. |
| PDF generation | ReportLab, fpdf2, browser HTML-to-PDF | fpdf2 | 2.8.8 | Easy, reliable, sufficient for simple assignment reports with minimal overhead. |
| DOCX generation | `python-docx`, `docxtpl` | `python-docx` | 1.2.0 | Straightforward and transparent for document generation without template overhead. |
| Email | stdlib `email` + `smtplib`, provider APIs, mail libraries | Python stdlib `email` + `smtplib` | Python 3.11.x | Best for local message construction and validation without credentials or external dependencies. |
| Tic-tac-toe move logic | Random, heuristic, minimax, minimax + alpha-beta | Minimax + alpha-beta | Python 3.11.x | Strong correctness and deterministic behavior on a 3x3 board without excessive complexity. |
| Rewards design | Fixed, weighted, streak, hybrid | Hybrid reward model | Python 3.11.x | Balances explainability, predictability, and meaningful incentives without obvious exploitability. |
| Automated/browser testing | Playwright, Selenium, AppTest | Playwright | 1.62.0 | Best end-to-end browser realism and CI suitability for Streamlit-style app testing. |
| Collaboration workflow | GitHub, GitLab, Bitbucket | GitHub | Evaluation validated local Git behavior | Best mix of familiarity, issue/PR tooling, and senior-design team workflow fit. |

## Overall Candidate Results

### CSV and data processing
| Candidate | Data handling | Suitability |
|---|---|---|
| Python stdlib `csv` | Strong for small datasets | Very High |
| Pandas | Excellent for spreadsheet-like transforms | High |
| Polars | Excellent columnar processing | High |

### Persistent data storage
| Candidate | CRUD/query strength | Suitability |
|---|---|---|
| SQLite | Very strong | Very High |
| JSON file | Simple but manual | High |
| TinyDB | Good but lighter than SQLite | Moderate-High |

### PDF generation
| Candidate | Simplicity | Formatting control | Suitability |
|---|---|---|---|
| fpdf2 | Very High | Moderate | High |
| ReportLab | High | Very High | High |
| Browser HTML-to-PDF | Moderate | Very High | Moderate |

### DOCX generation
| Candidate | Usage simplicity | Template power | Suitability |
|---|---|---|---|
| `python-docx` | Very High | Moderate | Very High |
| `docxtpl` | Moderate | High | High |

### Email
| Candidate | Local reliability | External dependency risk | Suitability |
|---|---|---|---|
| Python stdlib `email` + `smtplib` | Very High | Moderate at runtime | High |
| provider API/client | Moderate | High | Moderate |

### Tic-tac-toe logic
| Candidate | Correctness | Complexity | Suitability |
|---|---|---|---|
| Random | Very Low | Very Low | Poor |
| Heuristic | Moderate | Low | Acceptable |
| Minimax | High | Moderate | Strong |
| Minimax + alpha-beta | High | Low-Moderate | Strongest |

### Rewards
| Candidate | Predictability | Explainability | Suitability |
|---|---|---|---|
| Fixed points | Very High | Very High | High |
| Weighted points | High | High | Very High |
| Streak-based | Moderate | Moderate | Moderate |
| Hybrid | High | High | Very High |

### Automated/browser testing
| Candidate | Realism | CI suitability | Suitability |
|---|---|---|---|
| Playwright | Very High | Very High | Very High |
| Selenium | Very High | High | High |
| AppTest | Medium | High | High for Streamlit-only logic |

### Development collaboration workflow
| Candidate | Team fit | Issue/PR workflow | Suitability |
|---|---|---|---|
| GitHub | Very High | Very High | Very High |
| GitLab | High | Very High | High |
| Bitbucket | Moderate | Strong | Moderate |

## Development Collaboration Workflow

`Issue/Task -> Feature Branch -> Development -> Local Tests -> Commit -> Push -> Pull Request -> Peer Review -> Merge`

Recommended lightweight conventions:

- Branch naming: `feature/<short-name>`, `fix/<issue-name>`, `docs/<topic>`
- Commit messages: concise, action-oriented, and issue-linked where possible
- Pull requests: include short rationale, changed files, and test status
- Review before merge: at least one human review for nontrivial changes
- Keep `main` working: merge only tested and reasonably complete changes

## Validation Status

| Evaluation area | Status |
|---|---|
| CSV and data processing | Practical tests covered the full comparison |
| Persistent data storage | Practical tests covered the full comparison |
| PDF generation | Practical tests covered the full comparison |
| DOCX generation | Practical tests covered the full comparison |
| Email | Practical tests covered message construction only |
| Tic-tac-toe | Practical tests covered the full comparison |
| Rewards | Deterministic scenarios tested the reward models |
| Automated/browser testing | Practical tests partially covered the baseline approach |
| Collaboration workflow | Documentation and workflow design supplied the primary evidence |

## Open Questions / Follow-up

- Determine whether Folio will require richer report templating or a generated-output workflow beyond simple PDF and DOCX exports.
- Determine whether the team should expand browser testing into full CI pipeline checks after the UI becomes more complex.
- Explore a richer reward model only if user retention or gamification becomes a real product requirement.

## Selection confirmation

The evidence confirms the proposed baseline for Python, Streamlit, SQLite, `python-docx`, standard-library email, and GitHub. Python, Streamlit, SQLite, `python-docx`, standard-library email, and GitHub provide practical, low-overhead choices for Folio's early scope. The project team should reconsider Pandas or Polars only if Folio grows to require heavier analytical processing; the baseline does not need either library.
