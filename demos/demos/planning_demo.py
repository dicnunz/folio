"""Small runnable demonstration of Folio scheduling behavior."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
   sys.path.insert(0, str(PROJECT_ROOT))

from src import scheduling


def main():
   schedule = scheduling.Schedule()

   print("--- Folio Planning/Scheduling Demo ---\n")

   # Create some tasks
   task1 = scheduling.Task(1, 101, "Task 1", 10, 20)  # 'Control' task
   task2 = scheduling.Task(2, 102, "Task 2", 15, 25)  # Overlaps with task1
   task3 = scheduling.Task(3, 103, "Task 3", 30, 40)  # No overlap

   # Add the first task
   conflicts1 = schedule.add_task(task1)
   print(f"Added Task 1. Conflicts: {conflicts1}")

   # Add the second task and check for conflicts
   conflicts2 = schedule.add_task(task2)
   print(
      f"Added Task 2. Conflicts: "
      f"{[task.task_id for task in conflicts2]}"
   )

   # Add the third task and check for conflicts
   conflicts3 = schedule.add_task(task3)
   print(f"Added Task 3. Conflicts: {conflicts3}")

   print("\nFinal schedule:")
   for task in schedule.get_tasks():
      print(
         f"  Task {task.task_id}: plan {task.plan_id}, "
         f"time {task.start_time}-{task.end_time}"
      )

   print("\nConflicts are reported without deleting or moving either task.")
   print("Student choice is preserved.")


if __name__ == "__main__":
   main()
