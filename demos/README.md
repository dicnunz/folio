# Folio M1 File Purposes

This document explains the purpose of each current source, demo, and test file used for the Folio Milestone 1 technical proofs.

## Project Structure

```text
demos/
├── csv_sqlite_demo.py
├── planning_demo.py
└── tictactoe_demo.py

src/
├── csv_storage.py
├── rewards.py
├── scheduling.py
└── tictactoe.py

tests/
├── test_csv_storage.py
├── test_rewards.py
├── test_scheduling.py
└── test_tictactoe.py
```

The project follows a simple separation of responsibilities:

- `src/` contains reusable application logic.
- `demos/` contains small runnable examples that demonstrate the logic.
- `tests/` contains automated correctness tests for the corresponding source modules.

The demo files should stay lightweight and should call the real logic in `src/` rather than reimplementing it.

---

## `demos/`

### `demos/csv_sqlite_demo.py`

**Purpose:**  
Provides a small runnable demonstration of the CSV-to-SQLite workflow.

The demo should show that Folio can:

- read a small CSV file,
- validate imported data,
- identify invalid or duplicate records,
- store valid records in SQLite,
- and query the database afterward to confirm that the data was stored.

This file should use functions from `src/csv_storage.py` rather than implementing CSV parsing or database logic itself.

Example launch command:

```bash
python demos/csv_sqlite_demo.py
```

---

### `demos/planning_demo.py`

**Purpose:**  
Provides a simple runnable demonstration of planning and scheduling behavior.

The demo should show that Folio can:

- create or represent tasks from one or more plans,
- assign tasks to times,
- detect overlapping schedule entries,
- detect cross-plan collisions,
- and preserve student choice rather than silently deleting, replacing, or rescheduling a conflicting task.

This file should use the scheduling logic defined in `src/scheduling.py`.

Example launch command:

```bash
python demos/planning_demo.py
```

---

### `demos/tictactoe_demo.py`

**Purpose:**  
Provides a simple command-line tic-tac-toe demonstration.

The demo should show that Folio can:

- initialize a legal 3x3 game board,
- randomly select the starting player,
- accept valid player moves,
- reject illegal moves,
- allow the computer to choose moves,
- detect wins, losses, and ties,
- and start a new game after a game ends.

The computer move logic should use the selected minimax algorithm with alpha-beta pruning from `src/tictactoe.py`.

Example launch command:

```bash
python demos/tictactoe_demo.py
```

---

## `src/`

### `src/csv_storage.py`

**Purpose:**  
Contains the reusable CSV validation and SQLite persistence logic.

Responsibilities may include:

- opening and reading CSV files using Python's standard-library `csv` module,
- validating required fields,
- normalizing imported values,
- detecting malformed records,
- detecting duplicate records,
- initializing the SQLite database and schema,
- inserting valid records,
- preserving source information such as whether a record came from CSV,
- and querying saved records.

This module should contain the real data-import and persistence behavior used by both the demo and the automated tests.

---

### `src/rewards.py`

**Purpose:**  
Contains task-completion reward accounting.

This module should keep reward systems separate so that game moves, XP, points, and later reward features do not accidentally share the same state.

Responsibilities may include:

- recording completed task IDs,
- preventing the same task from awarding rewards more than once,
- awarding exactly one earned tic-tac-toe move for an eligible completed task,
- calculating XP,
- calculating points,
- consuming earned game moves,
- handling lost turns without incorrectly modifying unrelated rewards,
- and exposing the current reward state.

The design should make it possible for planning features to remain usable independently of the game and reward system.

---

### `src/scheduling.py`

**Purpose:**  
Contains reusable planning and scheduling logic.

Responsibilities may include:

- representing scheduled tasks,
- associating tasks with plans,
- validating task names and time ranges,
- adding tasks to a schedule,
- detecting duplicate tasks,
- detecting overlapping time ranges,
- detecting collisions between tasks from different plans,
- rescheduling tasks,
- and preserving the student's original choices when conflicts occur.

The scheduling logic should report conflicts rather than silently resolving them without student input.

---

### `src/tictactoe.py`

**Purpose:**  
Contains the reusable tic-tac-toe game engine and computer move logic.

Responsibilities may include:

- maintaining the game board,
- tracking the current player,
- checking whether a move is legal,
- applying moves,
- determining legal moves,
- detecting winning board states,
- detecting ties,
- resetting the game,
- randomly selecting the starting player,
- and choosing computer moves using minimax with alpha-beta pruning.

This file should focus only on game rules and game-state logic. It should not contain CSV, scheduling, or general reward-accounting behavior.

---

## `tests/`

### `tests/test_csv_storage.py`

**Purpose:**  
Verifies that the CSV and SQLite workflow behaves correctly.

Tests should cover behavior such as:

- accepting valid rows,
- rejecting missing required values,
- rejecting malformed dates or scores,
- detecting duplicate data,
- inserting valid records into SQLite,
- preventing duplicate database records where appropriate,
- preserving source labels,
- and correctly summarizing mixed imports containing valid, invalid, and duplicate rows.

Tests should use temporary files or temporary databases where practical so that test runs do not modify normal project data.

---

### `tests/test_rewards.py`

**Purpose:**  
Verifies reward and earned-move correctness.

Tests should cover behavior such as:

- one completed task earning one game move,
- XP being awarded correctly,
- points being awarded correctly,
- the same task not being rewarded twice,
- separate tasks earning separate rewards,
- consuming an earned game move,
- preventing moves from being consumed when none are available,
- lost turns not creating rewards,
- consuming a game move not changing XP or points,
- and game resets not incorrectly resetting unrelated reward state.

This test file is especially important for proving that earned game moves and general reward accounting remain separate.

---

### `tests/test_scheduling.py`

**Purpose:**  
Verifies planning and scheduling correctness.

Tests should cover behavior such as:

- adding valid tasks,
- rejecting invalid time ranges,
- rejecting incomplete task input,
- allowing adjacent non-overlapping tasks,
- detecting overlapping tasks,
- detecting cross-plan collisions,
- preserving both tasks when a conflict occurs,
- preventing silent automatic rescheduling,
- detecting duplicates,
- and correctly handling explicit rescheduling requests.

These tests provide evidence that Folio can combine tasks from multiple active plans without overriding student choice.

---

### `tests/test_tictactoe.py`

**Purpose:**  
Verifies tic-tac-toe game correctness.

Tests should cover behavior such as:

- starting with an empty board,
- selecting a valid starting player,
- accepting legal moves,
- rejecting occupied or out-of-range moves,
- detecting horizontal, vertical, and diagonal wins,
- detecting ties,
- detecting computer wins,
- resetting the board correctly for a new game,
- clearing previous winner state,
- ensuring minimax selects legal moves,
- taking an immediate winning move when available,
- blocking an immediate player win when appropriate,
- and preventing the computer from overwriting occupied cells.

These tests provide evidence that the game behaves consistently before it is integrated into the full Folio application.

---

## Design Principle

The intended dependency direction is:

```text
demos/  ─────►  src/
tests/  ─────►  src/
```

The `src/` modules should not depend on the demo or test files.

Keeping the application logic in `src/` makes it possible to reuse the same tested logic later in the Streamlit interface without rewriting the underlying behavior.

## TEST RESULTS TO .TXT

`python3.11 -m pytest -v > test_results.txt`

## EXECUTE DEMOS

```#!/bin/bash
python3.11 -m demos.planning_demo && \
python3.11 -m demos.csv_sqlite_demo && \
python3.11 -m demos.tictactoe_demo
```
