"""Minimal coursework service wiring until the CSE-19 screens are available."""
import streamlit as st


def show_result(result, message):
    if result["success"]:
        st.success(message)
    else:
        for error in result["errors"]:
            st.error(f"{error['field']}: {error['message']}")


def render_coursework(repository, service):
    st.header("Coursework")
    with st.form("create_coursework"):
        course = st.text_input("Course")
        name = st.text_input("Assignment name")
        due = st.text_input("Due date (YYYY-MM-DD)")
        score = st.text_input("Score (optional)")
        save = st.form_submit_button("Save coursework")
    if save:
        show_result(service.create_coursework({"course": course, "item_name": name,
                    "due_date": due, "score": score}), "Coursework saved.")

    st.subheader("Import CSV")
    st.caption("Required columns: course, item_name, due_date (YYYY-MM-DD). Optional: score (numeric). UTF-8 CSV; duplicates use the three required fields.")
    upload = st.file_uploader("Coursework CSV", type=["csv"])
    if st.button("Import coursework", disabled=upload is None):
        upload.seek(0)
        result = service.import_coursework_csv(upload, source=upload.name)
        st.write(f"Accepted: {result['accepted_count']}; rejected: {result['rejected_count']}")
        for message in result["file_errors"] + result["storage_errors"]:
            st.error(message)
        for row in result["errors"]:
            st.error(f"{row['source']}, line {row['row_number']}: " + "; ".join(row["errors"]))
        if result["success"]:
            st.success("Import processed.")

    records = repository.restore_saved_application_state()["coursework"]
    if records:
        by_id = {row["id"]: row for row in records}
        record_id = st.selectbox("Saved coursework", list(by_id),
            format_func=lambda identifier: f"{by_id[identifier]['course']} — {by_id[identifier]['item_name']} (#{identifier})")
        row = by_id[record_id]
        with st.form(f"edit_{record_id}"):
            course = st.text_input("Edit course", row["course"])
            name = st.text_input("Edit assignment name", row["item_name"])
            due = st.text_input("Edit due date (YYYY-MM-DD)", row["due_date"])
            score = st.text_input("Edit score (optional)", "" if row["score"] is None else str(row["score"]))
            edit = st.form_submit_button("Save changes")
        if edit:
            show_result(service.edit_coursework(record_id, {"course": course, "item_name": name,
                        "due_date": due, "score": score}), "Coursework changes saved.")
        if st.button("Delete selected coursework"):
            show_result(service.delete_coursework(record_id), "Coursework deleted.")
    records = repository.restore_saved_application_state()["coursework"]
    if records:
        st.dataframe(records, hide_index=True)
    else:
        st.info("No saved coursework yet.")
