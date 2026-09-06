# Folio

A senior project at Florida Institute of Technology by **Nicholas Dunzelman and Caleb Brooks**, advised by **Dr. David Luginbuhl**.

Folio is a student academic planning app in development. It is intended to help students turn coursework into manageable tasks, combine tasks from multiple plans into one schedule, and follow through with optional task-completion rewards.

## Current status

This repository currently contains the project website and planning documents. The application features below are planned, not a completed product.

- [Project website](https://dicnunz.github.io/folio/)
- [Project plan](docs/documents/first-semester/project-plan/project-plan-2026-08-30.pdf)
- [Plan presentation](docs/documents/first-semester/project-plan/plan-presentation-1.pdf)

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
