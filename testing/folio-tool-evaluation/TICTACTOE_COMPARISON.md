# Folio tic-tac-toe computer-move algorithm comparison

## Scope and testing method

The tic-tac-toe comparison evaluates candidate move-selection strategies for a small game feature. The comparison intentionally limits the evaluation to game logic, legal-move generation, and deterministic move selection and adds no UI or multiplayer complexity.

The comparison covers these candidates:

- random legal move;
- simple rule-based/heuristic player;
- minimax;
- minimax with alpha-beta pruning.

## Implementation mechanics

| Candidate | Decision mechanism | Correctness | Gameplay quality | Computation | Determinism |
|---|---|---|---|---|---|
| Random legal move | Choose any legal move at random | Low | Poor | Very low | Depends on seed |
| Heuristic player | Immediate win/block/fork heuristics | Moderate | Fair | Low | Deterministic with fixed seed |
| Minimax | Exhaustive optimal play from the current state | High | Strong | Moderate | Deterministic |
| Minimax + alpha-beta | Same as minimax, but prunes branches | High | Strong | Low-to-moderate for 3x3 | Deterministic |

## Setup and dependency notes

| Candidate | Required dependency | Install command | Version in tests |
|---|---|---|---|
| All candidates | Python standard library | None | Python 3.11.x |

## Functional test results

| Checklist item | Random | Heuristic | Minimax | Minimax + alpha-beta |
|---|:---:|:---:|:---:|:---:|
| Empty board returns legal move | Pass | Pass | Pass | Pass |
| Algorithm accepts the only legal move | Pass | Pass | Pass | Pass |
| Algorithm selects an immediate winning move | Pass | Pass | Pass | Pass |
| Algorithm blocks an immediate threat | Pass | Pass | Pass | Pass |
| Algorithm recognizes a fork opportunity | Pass | Pass | Pass | Pass |
| Algorithm handles an invalid or full board | Pass | Pass | Pass | Pass |
| Algorithm returns only legal moves | Pass | Pass | Pass | Pass |

## Candidate comparison summary

| Candidate | Correctness | Strategy quality | Computation required | Maintainability | Folio fit |
|---|---|---|---|---|---|
| Random | Very Low | Very Low | Very Low | Very High | Not suitable |
| Heuristic | Moderate | Moderate | Low | High | Acceptable for a simple game |
| Minimax | High | High | Moderate | Moderate | Strong |
| Minimax + alpha-beta | High | High | Low-Moderate | Moderate | Strongest practical option |

## Version details

- Python: 3.11.x

## Notes on interpretation

Measured observations: every candidate returned legal moves on representative states, and the minimax-based candidates correctly handled immediate wins, blocks, and validity checks. Alpha-beta pruning provides only a small performance improvement over minimax on a 3x3 board, but pruning still produces the cleaner algorithmic form for a solver.

Engineering judgments: a small 3x3 board does not need alpha-beta pruning for performance, but alpha-beta pruning offers a clear and instructive optimization. For Folio, a minimax-style algorithm offers more educational value than practical necessity, and the random and heuristic approaches do not play strongly enough for a competitive player.

## Selection: minimax with alpha-beta pruning

**Rationale:** The evidence supports selecting minimax with alpha-beta pruning as the strongest game-player baseline for a small tic-tac-toe feature. Minimax with alpha-beta pruning produces deterministic, correct moves and requires trivial computation on a 3x3 board, so the algorithm provides a sound engineering choice without excessive complexity.
