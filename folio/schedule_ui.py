"""Combined active-plan schedule and student-chosen conflict correction."""
from datetime import date, timedelta
import streamlit as st

from demos.src.scheduling import schedule_window
from .schedule_service import ScheduleService


def describe_task(row):
    return (f"Task #{row['id']} — {row['name']} | {row['course']} / {row['plan']} "
            f"(plan #{row['plan_id']}) | {row['start_time']} → {row['end_time']}")


def render_schedule(repository):
    service = ScheduleService(repository)
    st.header("Combined schedule")
    st.caption("Active plans only. Times are local; weeks run Monday–Sunday. Touching times do not conflict.")
    view = st.radio("Schedule view", ["Daily", "Weekly"], index=1, horizontal=True, key="schedule_view")
    selected_date = st.date_input("Schedule date", value=date.today(), key="schedule_date")
    st.button("Refresh schedule", help="Reload changes saved in another screen or session.")
    schedule = service.get_schedule()
    visible = schedule_window(schedule["tasks"], selected_date, view)
    by_id = {row["id"]: row for row in schedule["tasks"]}

    # Handle a submission before rendering rows, so the displayed schedule is current.
    if visible:
        selected_id = st.selectbox("Task to correct", [row["id"] for row in visible],
            format_func=lambda key: f"#{key} — {by_id[key]['name']} | {by_id[key]['course']} / {by_id[key]['plan']}")
        task = by_id[selected_id]
        with st.form(f"correct_task_{selected_id}_{task['start_time']}_{task['end_time']}"):
            st.caption(f"Saved: {task['start_time']} → {task['end_time']}. Enter both date and time as YYYY-MM-DDTHH:MM.")
            start = st.text_input("New start time", value=task["start_time"])
            end = st.text_input("New end time", value=task["end_time"])
            submitted = st.form_submit_button("Save corrected times")
        if submitted:
            result = service.reschedule_task(selected_id, start, end,
                expected_times=(task["start_time"], task["end_time"]))
            if result["success"]:
                st.success(f"Task #{selected_id} saved: {result['record']['start_time']} → {result['record']['end_time']}.")
            else:
                for error in result["errors"]:
                    st.error(f"{error['field']}: {error['message']}")
                if result["conflicts"]:
                    st.write(f"Proposed for task #{selected_id}: {start} → {end}")
                    for conflict in result["conflicts"]:
                        st.warning(describe_task(conflict))
            schedule = service.get_schedule()
            visible = schedule_window(schedule["tasks"], selected_date, view)
            by_id = {row["id"]: row for row in schedule["tasks"]}

    for problem in schedule["errors"]:
        st.error(f"Task #{problem['task_id']} in plan #{problem['plan_id']} cannot be placed: " +
                 "; ".join(error["message"] for error in problem["errors"]))
    first = selected_date if view == "Daily" else selected_date - timedelta(days=selected_date.weekday())
    last = first if view == "Daily" else first + timedelta(days=6)
    st.subheader(f"{view} schedule: {first.isoformat()} to {last.isoformat()}")
    rows = [{"Task ID": row["id"], "Task": row["name"], "Course": row["course"],
             "Plan": row["plan"], "Plan ID": row["plan_id"], "Start": row["start_time"],
             "End": row["end_time"], "Conflicts": ("⚠ " + ", ".join(f"#{key}" for key in row["conflict_ids"])) if row["conflict_ids"] else "None"}
            for row in visible]
    st.dataframe(rows, hide_index=True, width="stretch")
    if not visible:
        st.info("No tasks from active plans in this period.")
    elif not any(row["conflict_ids"] for row in visible) and not schedule["errors"]:
        st.success("No conflicts in this period.")
    pairs = set()
    for row in visible:
        for other_id in row["conflict_ids"]:
            pair = tuple(sorted((row["id"], other_id)))
            if pair not in pairs:
                pairs.add(pair)
                other = by_id[other_id]
                overlap_start = max(row["start_time"], other["start_time"])
                overlap_end = min(row["end_time"], other["end_time"])
                st.warning(f"Conflict: {describe_task(row)}\n\nOverlaps {describe_task(other)}\n\nOverlap: {overlap_start} → {overlap_end}. Choose corrected times above.")
