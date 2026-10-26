"""Run with: python -m streamlit run app.py."""
import streamlit as st

from demos.src.coursework_service import RepositoryError
from folio.application import open_application
from folio.coursework_ui import render_coursework
from folio.schedule_ui import render_schedule

st.set_page_config(page_title="Folio", layout="wide")
st.title("Folio")
st.caption("Academic planning • saved locally")

try:
    repository, coursework_service = open_application()
    render_coursework(repository, coursework_service)
    render_schedule(repository)
    state = repository.restore_saved_application_state()
    st.header("Saved plans")
    if not state["plans"]:
        st.info("No saved plans yet.")
    else:
        plans = {plan["id"]: plan for plan in state["plans"]}
        selected = st.selectbox("Plan", list(plans), format_func=lambda key: f"{plans[key]['name']} (#{key})")
        if st.button("Open saved plan"):
            st.session_state["open_plan"] = selected
        if st.session_state.get("open_plan") in plans:
            aggregate = repository.get_plan(st.session_state["open_plan"])
            plan = aggregate["plan"]
            coursework = next(row for row in state["coursework"] if row["id"] == plan["coursework_id"])
            st.subheader(plan["name"])
            st.write(f"Course: {coursework['course']} | Assignment: {coursework['item_name']}")
            st.write(plan["notes"])
            if aggregate["tasks"]:
                st.dataframe(aggregate["tasks"], hide_index=True)
            if aggregate["feedback"]:
                st.subheader("Entered feedback")
                st.dataframe(aggregate["feedback"], hide_index=True)

except RepositoryError as error:
    st.error(str(error))
    st.stop()
