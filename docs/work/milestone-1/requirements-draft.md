# Folio Requirement Document - Working Draft

Status: **not final**. Nicholas's assigned half is drafted below. Caleb's CSE-10 half is still pending and must be merged and cross-reviewed before this document can become the Milestone 1 Requirement PDF.

## 1. Purpose and scope

Folio is a student academic-planning system intended to help students select coursework to address, create and revise improvement plans, combine planned work into a schedule, optionally request instructor feedback, and follow through with task-completion support while preserving student control over what is shared.

The final document must describe what the system is required to do. Design choices and implementation details belong in the Design Document.

## 2. Nicholas half - student workflow, sharing, follow-through, privacy

See [requirements-nicholas.md](requirements-nicholas.md). Its requirement IDs are reserved as:

- WF-01 through WF-13
- FT-01 through FT-07
- EN-01 through EN-02
- PR-01 through PR-06
- INT-01 through INT-04
- PERF-01 through PERF-03

## 3. Caleb half - data, scheduling, game/reward correctness

Pending CSE-10. Reserve these ID ranges to prevent collisions during merge:

- DATA-01 onward: manual/CSV course data and validation
- STORE-01 onward: persistence/storage
- SCHED-01 onward: cross-plan scheduling and conflict behavior
- GAME-01 onward: tic-tac-toe correctness
- REWARD-01 onward: XP/points/levels/badges/cosmetics correctness
- PERF-DATA-01 onward: any data/scheduling/game performance requirements

## 4. Merge checklist

Before calling the combined Requirement Document complete:

1. Merge Caleb's CSE-10 requirements into the reserved sections.
2. Confirm every statement has one unique ID and one required behavior.
3. Remove duplicates and resolve contradictions.
4. Confirm all requirements are necessary, feasible, unambiguous, and verifiable.
5. Confirm functional, user/system-interface, and performance requirements are present.
6. Resolve all TBR performance values with the advisor/client or explicitly carry approved TBRs.
7. Cross-review both halves and record review evidence.
8. Format the combined document to at least 4 single-spaced pages, 12-point type, 1-inch margins.
9. Export the final PDF as `docs/documents/first-semester/milestone-1/requirement.pdf`.
10. Verify the Requirement link on the live project website.

## Sources

- Approved Folio First Semester Project Plan.
- Florida Tech Requirement/Design/Test guidelines: https://cs.fit.edu/~pkc/classes/seniorProjects/document.html
- NASA Systems Engineering Handbook Appendix C: https://www.nasa.gov/reference/system-engineering-handbook-appendix/
