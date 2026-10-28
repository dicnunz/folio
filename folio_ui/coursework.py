"""Coursework controls; validation and storage belong to the injected service."""

import re

import streamlit as st

from demos.src.coursework import OPTIONAL_COLUMNS, REQUIRED_COLUMNS
from demos.src.coursework_service import RepositoryError


FIELD_LABELS = {
    "course": "Course",
    "item_name": "Coursework name",
    "due_date": "Due date",
    "score": "Score",
    "start_time": "Start time",
    "end_time": "End time",
}


def error_message(error):
    message = error["message"]
    for field, label in FIELD_LABELS.items():
        message = re.sub(r"\b" + re.escape(field) + r"\b", label, message)
    return message


def show_errors(errors):
    for error in errors:
        st.error(error_message(error))


def show_import_result(result):
    st.write(f"Accepted: {result['accepted_count']} · Rejected: {result['rejected_count']}")
    st.caption(
        f"Invalid: {result['invalid_rows']} · Duplicates: {result['duplicate_rows']}. "
        "Duplicates count as rejected records."
    )
    for message in result["file_errors"] + result["storage_errors"]:
        st.error(message)
    for row in result["errors"]:
        location = f"Row {row['row_number']}"
        if row.get("end_row_number", row["row_number"]) != row["row_number"]:
            location += f"–{row['end_row_number']}"
        for error in row["field_errors"]:
            st.error(f"{result['source']} · {location}: {error_message(error)}")
    if result["success"] and result["total_rows"] == 0:
        st.info("The file contains a header but no coursework records. Nothing was added.")


def render_coursework(service):
    st.title("Coursework")
    st.caption("Enter coursework or import a CSV.")

    try:
        with service.repository.transaction() as repository:
            records = repository.list_records()
    except RepositoryError as error:
        st.error(str(error))
        st.info("Coursework could not be loaded. Existing data has not been replaced.")
        return

    by_id = {record["id"]: record for record in records}
    if st.session_state.get("selected_coursework_id") not in (None, *by_id):
        st.session_state["selected_coursework_id"] = None
        st.warning("The selected coursework is no longer available. Select another record.")
    planning_id = st.session_state.get("planning_coursework_id")
    if planning_id is not None:
        if planning_id in by_id:
            st.session_state["planning_coursework"] = dict(by_id[planning_id])
        else:
            st.session_state.pop("planning_coursework_id", None)
            st.session_state.pop("planning_coursework", None)
            st.warning("The coursework selected for planning is no longer available.")

    notice = st.session_state.pop("coursework_notice", None)
    if notice:
        st.success(notice)

    if records:
        st.dataframe(
            [{FIELD_LABELS.get(key, key.title()): record[key]
              for key in ("course", "item_name", "due_date", "score", "start_time", "end_time")}
             for record in records],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No coursework saved yet. Add your first item below.")

    def label(record_id):
        if record_id is None:
            return "New coursework"
        record = by_id[record_id]
        return f"{record['course']} · {record['item_name']} · {record['due_date']} (#{record_id})"

    # Keep the chosen ID independent of the widget: its labels/options change
    # after edits and imports, which can reset Streamlit's widget identity.
    options = [None, *by_id]

    def remember_selection():
        st.session_state["selected_coursework_id"] = st.session_state["coursework_picker"]

    selected_id = st.selectbox(
        "Coursework to edit or select", options,
        index=options.index(st.session_state.get("selected_coursework_id")),
        format_func=label, key="coursework_picker", on_change=remember_selection,
    )
    original = by_id.get(selected_id, {})
    revision = st.session_state.get("coursework_form_revision", 0)
    prefix = f"coursework_{selected_id}_{revision}"

    with st.form(f"{prefix}_form"):
        course = st.text_input("Course", value=original.get("course", ""), key=f"{prefix}_course")
        name = st.text_input("Coursework name", value=original.get("item_name", ""), key=f"{prefix}_name")
        due = st.text_input("Due date", value=original.get("due_date", ""), key=f"{prefix}_due")
        st.caption("Required: course, coursework name and a real date in YYYY-MM-DD format.")
        score_value = original.get("score")
        score = st.text_input(
            "Score (optional)", value="" if score_value is None else str(score_value),
            key=f"{prefix}_score",
        )
        st.caption("Score must be a finite number when supplied; leave blank for ungraded work.")
        start = st.text_input("Start time (optional, YYYY-MM-DDTHH:MM)",
                              value=original.get("start_time") or "", key=f"{prefix}_start")
        end = st.text_input("End time (optional, YYYY-MM-DDTHH:MM)",
                            value=original.get("end_time") or "", key=f"{prefix}_end")
        st.caption("For a class meeting or timed assessment, enter both local date/times. End must follow start.")
        save = st.form_submit_button("Save changes" if selected_id is not None else "Save coursework")

    if save:
        data = {"course": course, "item_name": name, "due_date": due, "score": score,
                "start_time": start, "end_time": end}
        result = (service.create_coursework(data) if selected_id is None
                  else service.edit_coursework(selected_id, data))
        if result["success"]:
            st.session_state["coursework_form_revision"] = revision + 1
            st.session_state["coursework_notice"] = "Coursework saved." if selected_id is None else "Changes saved."
            st.rerun()
        show_errors(result["errors"])

    if selected_id is not None:
        if st.button("Use for planning"):
            st.session_state["planning_coursework_id"] = selected_id
            st.session_state["planning_coursework"] = dict(original)
        if st.session_state.get("planning_coursework_id") == selected_id:
            st.info(f"Selected for planning: {original['item_name']} (#{selected_id}).")
        confirmed = st.checkbox("Confirm deletion of this coursework", key=f"delete_{selected_id}")
        if st.button("Delete coursework", disabled=not confirmed):
            result = service.delete_coursework(selected_id)
            if result["success"]:
                st.session_state["coursework_notice"] = "Coursework deleted."
                st.rerun()
            show_errors(result["errors"])

    st.subheader("Import coursework")
    st.write("Required CSV columns: " + ", ".join(f"`{field}`" for field in REQUIRED_COLUMNS) + ".")
    st.write("Optional CSV columns: " + ", ".join(f"`{field}`" for field in OPTIONAL_COLUMNS) + ".")
    st.caption(
        "Use exact column names and UTF-8 encoding. Dates: YYYY-MM-DD. Scores: finite numbers or blank. "
        "Times: YYYY-MM-DDTHH:MM in local time; supply both endpoints or leave both blank. "
        "Quote names containing commas. Records with the same course, name and due date are duplicates, "
        "even if their scores differ. Unsupported columns or unreadable files save nothing."
    )
    uploaded = st.file_uploader("Choose CSV", type=["csv"], key="coursework_upload")
    if st.button("Import CSV", disabled=uploaded is None):
        uploaded.seek(0)
        result = service.import_coursework_csv(uploaded, source=uploaded.name)
        st.session_state["coursework_import_result"] = result
        st.rerun()
    if "coursework_import_result" in st.session_state:
        show_import_result(st.session_state["coursework_import_result"])
