"""Scheduling domain rules, independent of Streamlit and SQLite."""
from datetime import date, datetime, time, timedelta
import re


def intervals_overlap(start_a, end_a, start_b, end_b):
   """Half-open intervals: touching endpoints do not overlap."""
   return start_a < end_b and end_a > start_b


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

      # Keep numeric M1 demos working, while supporting dated M2 tasks.
      if not isinstance(task.start_time, datetime):
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


def parse_task_time(value):
   """Parse the stored local minute-precision date/time contract."""
   if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
      raise ValueError("Use YYYY-MM-DDTHH:MM (24-hour local time).")
   try:
      return datetime.strptime(value, "%Y-%m-%dT%H:%M")
   except ValueError as error:
      raise ValueError("Use a valid date and time in YYYY-MM-DDTHH:MM format.") from error


def validate_task_times(start_time, end_time):
   """Collect both field errors without changing a stored task."""
   parsed, errors = {}, []
   for field, value in (("start_time", start_time), ("end_time", end_time)):
      try:
         parsed[field] = parse_task_time(value)
      except ValueError as error:
         errors.append({"field": field, "message": str(error)})
   if len(parsed) == 2 and parsed["start_time"] >= parsed["end_time"]:
      errors.append({"field": "end_time", "message": "End time must be later than start time."})
   return errors


def combine_active_tasks(state):
   """Join saved identities/context and annotate every active conflicting task.

   Saved overlaps are retained, never rescheduled or deduplicated on load.
   Malformed active intervals are reported explicitly rather than hidden.
   """
   plans = {plan["id"]: plan for plan in state["plans"] if plan["active"]}
   courses = {row["id"]: row for row in state["coursework"]}
   rows, errors, parsed = [], [], {}
   for task in state["tasks"]:
      plan = plans.get(task["plan_id"])
      if plan is None:
         continue
      problems = validate_task_times(task["start_time"], task["end_time"])
      if problems:
         errors.append({"task_id": task["id"], "plan_id": plan["id"], "errors": problems})
         continue
      course = courses[plan["coursework_id"]]
      row = {**task, "plan": plan["name"], "course": course["course"],
             "coursework_id": course["id"], "conflict_ids": []}
      parsed[row["id"]] = (parse_task_time(row["start_time"]), parse_task_time(row["end_time"]))
      rows.append(row)
   rows.sort(key=lambda row: (parsed[row["id"]][0], row["id"]))
   for index, first in enumerate(rows):
      start_a, end_a = parsed[first["id"]]
      for second in rows[index + 1:]:
         start_b, end_b = parsed[second["id"]]
         if start_b >= end_a:
            break
         if intervals_overlap(start_a, end_a, start_b, end_b):
            first["conflict_ids"].append(second["id"])
            second["conflict_ids"].append(first["id"])
   for row in rows:
      row["conflict_ids"].sort()
   return {"tasks": rows, "errors": errors}


def schedule_window(tasks, selected_date, view="Weekly"):
   """Include tasks intersecting a day or Monday–Sunday week, even overnight."""
   if type(selected_date) is not date or view not in ("Daily", "Weekly"):
      raise ValueError("Choose a date and Daily or Weekly view.")
   first = selected_date if view == "Daily" else selected_date - timedelta(days=selected_date.weekday())
   start = datetime.combine(first, time.min)
   end = start + timedelta(days=1 if view == "Daily" else 7)
   return [row for row in tasks if intervals_overlap(
      parse_task_time(row["start_time"]), parse_task_time(row["end_time"]), start, end)]


def combine_active_plan_tasks(state):
   """Join dated tasks to active plans and coursework without name deduplication.

   Times are local datetimes. Keep every stable task ID, even identical labels
   and intervals, and mark every member of each overlapping pair.
   """
   plans = {row['id']: row for row in state['plans'] if row['active']}
   coursework = {row['id']: row for row in state['coursework']}
   tasks = []
   for task in state['tasks']:
      plan = plans.get(task['plan_id'])
      if plan is None:
         continue
      start, end = (datetime.fromisoformat(task[field]) for field in ('start_time', 'end_time'))
      if start.tzinfo is not None or end.tzinfo is not None or start >= end:
         raise ValueError('Scheduled tasks need local times with end after start.')
      tasks.append({**task, 'course': coursework[plan['coursework_id']]['course'],
                    'plan_name': plan['name'], 'start': start, 'end': end, 'conflict_ids': []})
   tasks.sort(key=lambda task: (task['start'], task['id']))
   for index, first in enumerate(tasks):
      for second in tasks[index + 1:]:
         if second['start'] >= first['end']:
            break
         if first['start'] < second['end'] and first['end'] > second['start']:
            first['conflict_ids'].append(second['id'])
            second['conflict_ids'].append(first['id'])
   return tasks
