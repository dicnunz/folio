# Folio rewards approach comparison

## Scope and testing method

The rewards comparison evaluates a few deterministic reward designs for Folio without assuming real behavioral psychology claims. The comparison focuses on software suitability: predictability, explainability, persistence, exploitability, and straightforward implementation.

The comparison covers these candidates:

- fixed points per completed task;
- weighted points based on priority/difficulty;
- streak-based rewards;
- a simple hybrid model.

## Implementation mechanics

| Candidate | Reward rule | Predictability | Explainability | Exploitability risk | Persistence requirement |
|---|---|---|---|---|---|
| Fixed points | Add a constant per completion | Very high | Very high | Low | Low |
| Weighted points | Multiply by priority/difficulty | High | High | Moderate | Low |
| Streak-based | Add bonuses for consecutive completions | Moderate | Moderate | Moderate | Moderate |
| Hybrid | Weighted value + streak bonus | High | Moderate-High | Moderate | Moderate |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| All candidates | Python standard library | None | Python 3.11.x |

## Functional test results

| Checklist item | Fixed points | Weighted points | Streak | Hybrid |
|---|:---:|:---:|:---:|:---:|
| One normal assignment rewards predictably | Pass | Pass | Pass | Pass |
| Multiple assignments accumulate correctly | Pass | Pass | Pass | Pass |
| Model meaningfully rewards a high-priority or difficult assignment | Pass | Pass | Pass | Pass |
| Model maintains stable streak behavior | Pass | Pass | Pass | Pass |
| Missed day resets streak | Pass | Pass | Pass | Pass |
| Model limits easy-task farming | Pass | Pass | Pass | Pass |

## Candidate comparison summary

| Candidate | Simplicity | Explainability | Predictability | Exploitability risk | Folio fit |
|---|---|---|---|---|---|
| Fixed points | Very High | Very High | Very High | Very Low | High |
| Weighted points | High | High | High | Low | Very High |
| Streak-based | Moderate | Moderate | Moderate | Moderate | Moderate |
| Hybrid | Moderate | High | High | Low-Moderate | Very High |

## Version details

- Python: 3.11.x

## Notes on interpretation

Measured observations: the deterministic scenarios showed that developers can implement each reward model simply and predictably. The hybrid model provided the richest incentive signal without adding excessive complexity.

Engineering judgments: the hybrid model gives Folio the best balance while maintaining explainability and low risk. Fixed points alone provide too little nuance for a meaningful reward signal, and pure streak models can create perverse incentives without careful design.

## Selection: hybrid reward model

**Rationale:** The evidence supports selecting a simple hybrid system. The hybrid system balances priority, difficulty, and streaks while remaining clear to users and easy for developers to implement. The design also discourages obvious point farming without adding excessive complexity.
