from src.rewards import RewardState


def test_one_task_earns_one_game_move():
    rewards = RewardState()

    result = rewards.complete_task(1)

    assert result["game_moves_awarded"] == 1
    assert rewards.earned_game_moves == 1


def test_task_awards_weighted_xp_and_points():
    rewards = RewardState()

    result = rewards.complete_task(1, task_weight=3)

    assert result["xp_awarded"] == 30
    assert result["points_awarded"] == 15
    assert rewards.xp == 30
    assert rewards.points == 15


def test_duplicate_task_completion_does_not_award_twice():
    rewards = RewardState()
    first = rewards.complete_task(42, task_weight=2)
    second = rewards.complete_task(42, task_weight=5)

    assert first["awarded"] is True
    assert second["awarded"] is False
    assert rewards.get_reward_state() == {
        "xp": 20,
        "points": 10,
        "earned_game_moves": 1,
        "completed_task_ids": {42},
    }


def test_two_different_tasks_earn_separate_rewards():
    rewards = RewardState()

    rewards.complete_task(1)
    rewards.complete_task(2)

    assert rewards.earned_game_moves == 2
    assert rewards.completed_task_ids == {1, 2}


def test_consuming_move_changes_only_move_count():
    rewards = RewardState()
    rewards.complete_task(1, task_weight=2)
    xp_before = rewards.xp
    points_before = rewards.points

    assert rewards.consume_game_move() is True
    assert rewards.earned_game_moves == 0
    assert rewards.xp == xp_before
    assert rewards.points == points_before


def test_cannot_consume_move_when_none_are_available():
    rewards = RewardState()

    assert rewards.consume_game_move() is False
    assert rewards.earned_game_moves == 0


def test_lost_turn_does_not_change_rewards():
    rewards = RewardState()
    rewards.complete_task(1)
    before = rewards.get_reward_state()

    assert rewards.lose_turn() is False
    assert rewards.get_reward_state() == before


def test_invalid_task_weight_is_rejected_without_processing_task():
    rewards = RewardState()

    try:
        rewards.complete_task(1, task_weight=0)
        assert False, "Expected an invalid-weight ValueError"
    except ValueError:
        pass

    assert rewards.get_reward_state()["completed_task_ids"] == set()
