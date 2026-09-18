from dataclasses import dataclass, field


@dataclass
class Task:
   title: str
   priority: str
   difficulty: str = "normal"
   completed: bool = False


@dataclass
class ScoreState:
   points: int = 0
   streak: int = 0
   last_day: str | None = None


def fixed_points(task):
   weights = {"Low": 5, "Medium": 10, "High": 15}
   return weights.get(task.priority, 0)


def weighted_points(task):
   base = fixed_points(task)
   multipliers = {"easy": 1.0, "normal": 1.2, "hard": 1.5}
   return int(base * multipliers.get(task.difficulty, 1.0))


def streak_points(task, state):
   points = weighted_points(task)
   if task.completed:
      state.streak += 1
      state.points += points + max(0, state.streak - 1) * 2
   else:
      state.streak = 0
   return state.points


def fixed_points_system(tasks):
   return sum(fixed_points(t) for t in tasks if t.completed)


def weighted_system(tasks):
   return sum(weighted_points(t) for t in tasks if t.completed)


def hybrid_system(tasks):
   state = ScoreState()
   for task in tasks:
      if task.completed:
            state.points += weighted_points(task) + max(0, state.streak) * 2
            state.streak += 1
      else:
            state.streak = 0
   return state.points


def test_fixed_points_for_normal_tasks():
   tasks = [Task("Reading", "Low", completed=True)]
   assert fixed_points_system(tasks) == 5


def test_weighted_points_for_high_priority_task():
   tasks = [Task("Design Review", "High", "hard", completed=True)]
   assert weighted_points(tasks[0]) == 22


def test_streak_rewards_are_cumulative():
   tasks = [Task("A", "Medium", completed=True), Task("B", "Medium", completed=True), Task("C", "Medium", completed=True)]
   assert hybrid_system(tasks) == 10 + 12 + 14


def test_missing_day_resets_streak():
   tasks = [Task("A", "Medium", completed=True), Task("B", "Medium", completed=False), Task("C", "Medium", completed=True)]
   assert hybrid_system(tasks) == 12 + 10


def test_repeated_easy_tasks_do_not_overinflate_points():
   tasks = [Task(f"Task {i}", "Low", "easy", completed=True) for i in range(5)]
   assert sum(weighted_points(t) for t in tasks) == 25
