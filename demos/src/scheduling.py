class Task:
   """Represent one scheduled task."""

   def __init__(self, task_id, plan_id, name, start_time, end_time):
      self.task_id = task_id
      self.plan_id = plan_id
      self.name = name
      self.start_time = start_time
      self.end_time = end_time


class Schedule:
   """Store tasks and report duplicate or scheduling conflicts."""

   def __init__(self):
      self.tasks: dict[int, Task] = {}
      self.task_signatures: set[tuple] = set()

   def _make_signature(self, task):
      """Return the fields that identify a true duplicate task."""
      return (task.plan_id, task.name, task.start_time, task.end_time)

   def _overlaps(self, task_a, task_b):
      """Return whether two half-open time intervals overlap."""
      return (
         task_a.start_time < task_b.end_time
         and task_b.start_time < task_a.end_time
      )

   def validate_task(self, task):
      """Validate a task before it is added or rescheduled."""
      if task.name is None or task.name.strip() == "":
         raise ValueError("Task name cannot be empty.")

      if task.start_time >= task.end_time:
         raise ValueError("Task start time must be before end time.")

      if task.start_time < 0 or task.end_time < 0:
         raise ValueError("Task start and end times must be non-negative.")

   def add_task(self, task):
      """Add a valid, unique task and return any time conflicts."""
      self.validate_task(task)

      if task.task_id in self.tasks:
         raise ValueError("A task with the given ID already exists.")

      signature = self._make_signature(task)
      if signature in self.task_signatures:
         raise ValueError("An identical task already exists.")

      conflicts = self.find_conflicts(task)
      self.tasks[task.task_id] = task
      self.task_signatures.add(signature)
      return conflicts

   def find_conflicts(self, task):
      """Return scheduled tasks that overlap with task, excluding itself."""
      return [
         existing_task
         for existing_task in self.tasks.values()
         if existing_task.task_id != task.task_id
         and self._overlaps(task, existing_task)
      ]

   def get_task(self, task_id):
      """Return a task by ID, or None when it is not scheduled."""
      return self.tasks.get(task_id)

   def get_tasks(self):
      """Return all scheduled tasks in insertion order."""
      return list(self.tasks.values())

   def get_tasks_for_plan(self, plan_id):
      """Return all scheduled tasks belonging to a plan."""
      return [task for task in self.tasks.values() if task.plan_id == plan_id]

   def remove_task(self, task_id):
      """Remove and return a task by ID, or return None if it is absent."""
      task = self.tasks.pop(task_id, None)
      if task is not None:
         self.task_signatures.discard(self._make_signature(task))
      return task

   def reschedule_task(self, task_id, new_start_time, new_end_time):
      """Reschedule a task if the proposed time does not conflict."""
      task = self.get_task(task_id)
      if task is None:
         raise ValueError("Task with the given ID not found.")

      proposed_task = Task(
         task.task_id,
         task.plan_id,
         task.name,
         new_start_time,
         new_end_time,
      )
      self.validate_task(proposed_task)

      old_signature = self._make_signature(task)
      new_signature = self._make_signature(proposed_task)
      if (
         new_signature != old_signature
         and new_signature in self.task_signatures
      ):
         raise ValueError("An identical task already exists.")

      conflicts = self.find_conflicts(proposed_task)
      if conflicts:
         return conflicts

      self.task_signatures.discard(old_signature)
      task.start_time = new_start_time
      task.end_time = new_end_time
      self.task_signatures.add(new_signature)
      return []
