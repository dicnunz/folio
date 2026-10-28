"""Session-isolated public demo. Run: streamlit run cloud_app.py."""
from pathlib import Path
from tempfile import TemporaryDirectory

import streamlit as st

from app import main

# Retain the owner across reruns; its finalizer removes the database when released.
if "_folio_demo_directory" not in st.session_state:
    st.session_state["_folio_demo_directory"] = TemporaryDirectory(prefix="folio-demo-")

demo_directory = st.session_state["_folio_demo_directory"]
main(
    database_path=Path(demo_directory.name) / "academic.sqlite3",
    storage_caption="Public demo: saved only for this session. Reloading or leaving may reset your work.",
)
