"""Reward accounting kept separate from game and scheduling state."""


class RewardState:
    """Track task rewards and earned tic-tac-toe moves."""

    def __init__(self):
        self.xp = 0
        self.points = 0
        self.earned_game_moves = 0
        self.processed_task_ids = set()
        self.completed_task_ids = set()

    def calculate_xp(self, task_weight):
        """Calculate XP using a small weight-based reward."""
        return 10 * task_weight

    def calculate_points(self, task_weight):
        """Calculate points separately from XP and game moves."""
        return 5 * task_weight

    def complete_task(self, task_id, task_weight=1):
        """Award a task once and return details about the result."""
        if task_id in self.processed_task_ids:
            return {
                "awarded": False,
                "xp_awarded": 0,
                "points_awarded": 0,
                "game_moves_awarded": 0,
            }

        if not isinstance(task_weight, int) or isinstance(task_weight, bool):
            raise ValueError("Task weight must be a positive integer.")
        if task_weight <= 0:
            raise ValueError("Task weight must be a positive integer.")

        xp_awarded = self.calculate_xp(task_weight)
        points_awarded = self.calculate_points(task_weight)

        self.processed_task_ids.add(task_id)
        self.completed_task_ids.add(task_id)
        self.xp += xp_awarded
        self.points += points_awarded
        self.earned_game_moves += 1

        return {
            "awarded": True,
            "xp_awarded": xp_awarded,
            "points_awarded": points_awarded,
            "game_moves_awarded": 1,
        }

    def consume_game_move(self):
        """Consume one earned move without changing XP or points."""
        if self.earned_game_moves == 0:
            return False
        self.earned_game_moves -= 1
        return True

    def lose_turn(self):
        """Record no reward changes for a lost turn."""
        return False

    def get_reward_state(self):
        """Return a snapshot of the current reward state."""
        return {
            "xp": self.xp,
            "points": self.points,
            "earned_game_moves": self.earned_game_moves,
            "completed_task_ids": set(self.completed_task_ids),
        }
