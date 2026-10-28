"""Folio's local academic workflows. Run: python -m streamlit run app.py."""
import streamlit as st

from demos.src.coursework_service import RepositoryError
from folio.application import open_application
from folio_ui.coursework import render_coursework


def main(database_path=None, storage_caption="Saved locally on this computer."):
    st.set_page_config(page_title="Folio v0.5", layout="centered")
    with st.sidebar:
        st.title("Folio v0.5")
        screen = st.radio("Workspace", ["Coursework", "Plan", "Schedule", "Share"], key="folio_screen")
        st.caption(storage_caption)

    try:
        repository, coursework_service = open_application(database_path)
        if screen == "Coursework":
            render_coursework(coursework_service)
        elif screen == "Plan":
            from folio_ui.planning import render_planning
            render_planning(repository)
        elif screen == "Schedule":
            from folio_ui.scheduling import render_schedule
            render_schedule(repository)
        elif screen == "Share":
            from folio_ui.sharing import render_sharing
            render_sharing(repository)
    except RepositoryError as error:
        st.error(str(error))
        st.stop()


if __name__ == "__main__":
    main()
