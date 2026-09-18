# Folio scheduling comparison

## Scope and testing method

The scheduling comparison isolates scheduling and planning behavior only. The comparison does not include Streamlit UI, SQLite, Pandas, email, rewards, authentication, or other Folio features.

The tests use the same representative scheduling scenarios for every candidate:

- create a task with a title and due date/time;
- determine whether a task is upcoming, due today, or overdue;
- sort multiple tasks by due date/time;
- represent a recurring task;
- determine the next occurrence of a recurring task;
- handle timezone-aware dates where applicable;
- reject or safely handle invalid date/time input;
- preserve predictable behavior around date boundaries.

All candidate tests use `test_scheduling.py`. The test file relies on fixed timestamps rather than the machine clock.

## Implementation mechanics

| Candidate | Task representation | Due-state logic | Recurrence model | Next-occurrence calculation | Timezone handling | Invalid input behavior | Boundary semantics | Framework-specific limitations |
|---|---|---|---|---|---|---|---|---|
| Python standard library (`datetime` + `zoneinfo`) | Plain dataclass object with `title` and `due_at` | Compare `due_at` to a fixed `now` and classify the task as `upcoming`, `due today`, or `overdue` | Developers must implement recurrence manually with a custom task object or simple interval rule | Loop over interval steps (`daily` or `weekly`) until the next value falls strictly after the reference point | `zoneinfo` provides native, explicit support; developers can easily normalize and convert aware datetimes | Reject invalid ISO-8601 or `datetime` input through `TypeError` or `ValueError` | Explicit boundary logic produces deterministic, predictable behavior | The standard library lacks a recurring-task abstraction, so developers must maintain all custom rules in application code |
| APScheduler | Small task dictionary or custom adapter storing trigger metadata alongside task fields | Use the same classification logic as the standard-library candidate; task metadata serves only as a container | Interval triggers (`IntervalTrigger`) provide built-in recurrence | The adapter calls `get_next_fire_time(None, reference)` and applies a small boundary correction to model “strictly after the current moment” | APScheduler supports timezone-aware triggers and datetimes well | The adapter rejects invalid values before task creation; library exceptions can surface when developers misconfigure a trigger | APScheduler includes the current scheduled fire when the reference time lands exactly on a boundary, so the test adjusts APScheduler's result for Folio's planning interpretation | APScheduler primarily targets background-job execution rather than task-planning semantics and exposes a broader API than Folio needs |
| `schedule` | Small task dictionary or custom adapter storing title, due date, and recurrence metadata | Use the same due-state classification logic as the other candidates | Job registration provides built-in recurring jobs, but the comparison still models task planning explicitly | The adapter manually calculates the next occurrence with interval arithmetic because `schedule` does not provide a task-planning abstraction | `schedule` provides limited timezone support, so developers usually handle timezones manually | The custom adapter rejects invalid input before creating a job | `schedule` supports simple everyday job semantics but lacks direct date-state queries for a planning model | `schedule` primarily runs scheduled jobs rather than general application scheduling logic or date-state planning queries |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Approximate application code required |
|---|---|---|---|
| Python standard library (`datetime` + `zoneinfo`) | None beyond Python 3.11+ | No additional install required | Small custom module with one dataclass and a few helper functions |
| APScheduler | `APScheduler` | `python -m pip install APScheduler` | Small adapter layer around interval triggers and task metadata |
| `schedule` | `schedule` | `python -m pip install schedule` | Small adapter layer plus custom recurrence logic for planning queries |

## Candidate comparison summary

| Candidate | Recurring scheduling | Timezone support | Ease of determining next run | Implementation complexity | Maintainability | Fit for Folio's expected scale |
|---|---|---|---|---|---|---|
| Python stdlib | Manual | Strong | High | Low to medium | High | Strong |
| APScheduler | Built in for job triggers | Good | Medium | Medium | Medium | Good for execution; not ideal for task-planning core |
| `schedule` | Built in for job execution | Limited/manual | Low to medium | Medium | Low to medium | Weak for planning-focused use |

## Version details

- Python: 3.11.x in the workspace virtual environment
- `pytest`: 9.1.1
- `APScheduler`: 3.11.3
- `schedule`: 1.2.2

## Notes on interpretation

The scheduling comparison treats planning and scheduling as application scheduling logic first, not background execution. Specifically, the comparison asks whether each library naturally supports Folio's task model: due-state classification, ordering, recurring task semantics, and next-occurrence queries. APScheduler and `schedule` mainly solve periodic background execution; both libraries provide useful capabilities, but neither library supplies a task-planning abstraction.

The deterministic test file and fixed timestamps produced the observed results. Engineering judgments reflect each candidate's practical fit for Folio's likely task-planning requirements and the semantic mismatch between background-job frameworks and task-management logic.
