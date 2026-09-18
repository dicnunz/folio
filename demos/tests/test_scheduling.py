from src.scheduling import Schedule, Task


def assert_value_error(action, expected_message):
    """Assert that an action raises ValueError with the expected text."""
    try:
        action()
    except ValueError as error:
        assert expected_message in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_valid_task_addition_and_lookup_by_id():
    schedule = Schedule()
    task = Task(1, 101, "Review Chapter", 10, 20)

    assert schedule.add_task(task) == []
    assert schedule.get_task(1) is task
    assert schedule.get_task(999) is None


def test_duplicate_task_id_is_rejected_without_replacing_task():
    schedule = Schedule()
    original = Task(1, 101, "Original", 10, 20)
    schedule.add_task(original)

    assert_value_error(
        lambda: schedule.add_task(Task(1, 202, "Replacement", 30, 40)),
        "ID already exists",
    )

    assert schedule.get_task(1) is original


def test_duplicate_signature_is_rejected_even_with_a_different_id():
    schedule = Schedule()
    schedule.add_task(Task(1, 101, "Review Chapter", 10, 20))

    assert_value_error(
        lambda: schedule.add_task(Task(2, 101, "Review Chapter", 10, 20)),
        "identical task",
    )

    assert len(schedule.get_tasks()) == 1


def test_adjacent_nonoverlapping_tasks_have_no_conflicts():
    schedule = Schedule()
    schedule.add_task(Task(1, 101, "First", 10, 20))

    conflicts = schedule.add_task(Task(2, 101, "Second", 20, 30))

    assert conflicts == []


def test_overlapping_cross_plan_tasks_report_conflict():
    schedule = Schedule()
    first = Task(1, 101, "Calculus", 10, 20)
    second = Task(2, 202, "Design", 15, 25)
    schedule.add_task(first)

    conflicts = schedule.add_task(second)

    assert conflicts == [first]


def test_conflicting_addition_preserves_both_student_choices():
    schedule = Schedule()
    first = Task(1, 101, "Calculus", 10, 20)
    second = Task(2, 202, "Design", 15, 25)
    schedule.add_task(first)

    schedule.add_task(second)

    assert schedule.get_tasks() == [first, second]
    assert (first.start_time, first.end_time) == (10, 20)
    assert (second.start_time, second.end_time) == (15, 25)


def test_get_tasks_for_plan_filters_tasks():
    schedule = Schedule()
    first = Task(1, 101, "First", 10, 20)
    second = Task(2, 202, "Second", 30, 40)
    third = Task(3, 101, "Third", 50, 60)
    for task in (first, second, third):
        schedule.add_task(task)

    assert schedule.get_tasks_for_plan(101) == [first, third]


def test_removal_updates_lookup_and_duplicate_signature_tracking():
    schedule = Schedule()
    task = Task(1, 101, "Review Chapter", 10, 20)
    schedule.add_task(task)

    assert schedule.remove_task(1) is task
    assert schedule.get_task(1) is None
    assert schedule.remove_task(1) is None
    assert schedule.add_task(Task(2, 101, "Review Chapter", 10, 20)) == []


def test_valid_reschedule_updates_time_and_signature():
    schedule = Schedule()
    task = Task(1, 101, "Review Chapter", 10, 20)
    schedule.add_task(task)

    conflicts = schedule.reschedule_task(1, 30, 40)

    assert conflicts == []
    assert (task.start_time, task.end_time) == (30, 40)
    assert (101, "Review Chapter", 10, 20) not in schedule.task_signatures
    assert (101, "Review Chapter", 30, 40) in schedule.task_signatures


def test_conflicting_reschedule_returns_conflict_and_keeps_original_time():
    schedule = Schedule()
    first = Task(1, 101, "First", 10, 20)
    second = Task(2, 202, "Second", 30, 40)
    schedule.add_task(first)
    schedule.add_task(second)

    conflicts = schedule.reschedule_task(1, 35, 45)

    assert conflicts == [second]
    assert (first.start_time, first.end_time) == (10, 20)
    assert (second.start_time, second.end_time) == (30, 40)


def test_invalid_or_missing_reschedule_is_rejected():
    schedule = Schedule()
    task = Task(1, 101, "First", 10, 20)
    schedule.add_task(task)

    assert_value_error(
        lambda: schedule.reschedule_task(1, 40, 30),
        "start time",
    )
    assert_value_error(
        lambda: schedule.reschedule_task(999, 30, 40),
        "not found",
    )

    assert (task.start_time, task.end_time) == (10, 20)
