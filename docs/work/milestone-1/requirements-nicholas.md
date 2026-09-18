# Folio Milestone 1 Requirements - Nicholas Half

Status: draft for team cross-review and advisor/client review.

## Scope

This half covers the areas assigned to Nicholas Dunzelman for CSE-9: coursework selection, editable planning templates, instructor sharing/feedback/revision, reminders/completion UX, optional encouragement, and privacy. Requirements state required behavior, not implementation.

## Functional requirements

- **WF-01** Folio shall allow the student to select an assignment, test, or other coursework item from available course information as the subject of a plan.
- **WF-02** Folio shall allow the student to choose a planning template for the selected coursework.
- **WF-03** Folio shall present the tasks suggested by the selected planning template before the plan is finalized.
- **WF-04** Folio shall allow the student to edit each suggested task before finalizing the plan.
- **WF-05** Folio shall allow the student to revise an existing plan after it has been created.
- **WF-06** Folio shall allow the student to export academic plan information as a PDF.
- **WF-07** Folio shall allow the student to export academic plan information as a DOCX.
- **WF-08** Folio shall prepare instructor-email content from academic plan information for student review.
- **WF-09** Folio shall require student review of prepared instructor-email content before any sharing action.
- **WF-10** Folio shall allow the student to accept an instructor suggestion before revising the plan from that suggestion.
- **WF-11** Folio shall allow the student to reject an instructor suggestion without revising the plan from that suggestion.
- **WF-12** Folio shall allow the student to adapt an instructor suggestion before applying it to the plan.
- **WF-13** Folio shall allow the student to use the planning workflow without instructor participation.
- **FT-01** Folio shall provide a daily view of scheduled tasks.
- **FT-02** Folio shall provide a weekly view of scheduled tasks.
- **FT-03** Folio shall allow the student to reschedule a scheduled task.
- **FT-04** Folio shall allow the student to configure reminders for scheduled tasks.
- **FT-05** Folio shall allow the student to mark a task complete.
- **FT-06** Folio shall display progress for each plan based on task completion.
- **FT-07** Folio shall provide a congratulatory response when the student completes a task.
- **EN-01** Folio shall allow the student to use planning features without participating in the game.
- **EN-02** Folio shall allow the student to use planning features without using rewards.

## Privacy requirements

- **PR-01** Folio shall allow the student to choose which academic plan information is prepared for instructor sharing.
- **PR-02** Folio shall exclude task-progress data from academic exports and prepared instructor emails.
- **PR-03** Folio shall exclude XP, points, levels, badges, and cosmetic-reward data from academic exports and prepared instructor emails.
- **PR-04** Folio shall exclude game-state, win, loss, tie, and move data from academic exports and prepared instructor emails.
- **PR-05** Folio shall present the exact academic content prepared for sharing before the student shares it.
- **PR-06** Folio shall use course information as planning context without inferring studying, attendance, participation, or effort outside Folio.

## Interface requirements

- **INT-01** Folio shall provide a student-facing interface for selecting coursework and creating or revising a plan.
- **INT-02** Folio shall provide a student-facing preview of PDF, DOCX, and prepared-email sharing outputs before sharing.
- **INT-03** Folio shall provide a student-facing control for configuring reminders.
- **INT-04** Folio shall support instructor feedback without requiring an instructor-facing Folio account or dashboard.

## Performance requirements - values to be resolved

The course requires performance requirements. The approved plan does not set quantitative response-time or capacity targets, so values are marked TBR rather than invented.

- **PERF-01** Folio shall complete an interactive plan-edit or save action within **TBR-1 seconds** under the agreed reference workload.
- **PERF-02** Folio shall generate a PDF, DOCX, or prepared-email preview within **TBR-2 seconds** for a plan containing up to **TBR-3 tasks**.
- **PERF-03** Folio shall reflect a task-completion or rescheduling action in the displayed plan state within **TBR-4 seconds**.

### TBR register

- **TBR-1:** interactive response-time threshold; resolve with advisor/client by Sep 23.
- **TBR-2:** export/preview response-time threshold; resolve with advisor/client by Sep 23.
- **TBR-3:** reference plan-size workload; resolve with advisor/client by Sep 23.
- **TBR-4:** state-update response-time threshold; resolve with advisor/client by Sep 23.

## Verification trace

| Requirement(s) | Verification method |
| --- | --- |
| WF-01-WF-05 | Demonstration using a plan from coursework selection through edit and revision |
| WF-06-WF-09 | Demonstration and output inspection using PDF, DOCX, and email-preview artifacts |
| WF-10-WF-13 | Demonstration of accept/reject/adapt paths and planning without instructor participation |
| FT-01-FT-07 | Demonstration of daily/weekly views, rescheduling, reminders, completion, progress, congratulations |
| EN-01-EN-02 | Demonstration with game/rewards unused |
| PR-01-PR-05 | Output inspection proving only student-selected academic information is prepared for sharing |
| PR-06 | Inspection plus tests showing no external-effort inference is produced |
| INT-01-INT-04 | Interface demonstration and inspection |
| PERF-01-PERF-03 | Timed test after TBR values are approved |

## Sources and drafting rules

Project behavior is derived from the approved Folio First Semester Project Plan. Document structure follows Florida Tech's Requirement Document guidance requiring functional, interface, and performance requirements. Wording follows NASA requirements guidance: unique IDs, "shall" statements, one requirement per statement, measurable/verifiable language, and requirements that state what is needed rather than how to implement it. Privacy requirements implement the approved Folio privacy boundary and NIST's manageability principle of granular administration/selective disclosure.

- https://cs.fit.edu/~pkc/classes/seniorProjects/document.html
- https://www.nasa.gov/reference/system-engineering-handbook-appendix/
- https://swehb.nasa.gov/spaces/SWEHBVB/pages/32604503/SWE-050%2B-%2BSoftware%2BRequirements
- https://csrc.nist.gov/glossary/term/manageability
