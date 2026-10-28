"""Password-gated shared demo with durable remote storage."""
import hmac
import os

import streamlit as st

from app import main


def setting(name):
    value = os.environ.get(name)
    if value is not None:
        return value
    try:
        return st.secrets.get(name, "")
    except FileNotFoundError:
        return ""


password = setting("FOLIO_DEMO_PASSWORD")
if not password:
    st.set_page_config(page_title="Folio v0.5", layout="centered")
    st.title("Folio v0.5")
    st.error("Demo access is not configured.")
    st.stop()


def unlock():
    supplied = st.session_state.pop("demo_password", "")
    st.session_state["demo_authenticated"] = hmac.compare_digest(
        supplied.encode("utf-8"), password.encode("utf-8")
    )
    st.session_state["demo_password_error"] = not st.session_state["demo_authenticated"]


if not st.session_state.get("demo_authenticated", False):
    st.set_page_config(page_title="Folio v0.5", layout="centered")
    st.title("Folio v0.5")
    with st.form("demo_access"):
        st.text_input("Demo password", type="password", key="demo_password")
        st.form_submit_button("Open Folio", on_click=unlock)
    if st.session_state.get("demo_password_error"):
        st.error("Incorrect password.")
    st.stop()

from folio.cloud_storage import CloudAcademicRepository

url, key, token = (setting(name) for name in
                   ("FOLIO_SUPABASE_URL", "FOLIO_SUPABASE_KEY", "FOLIO_STORAGE_TOKEN"))
if not all((url, key, token)):
    st.error("Demo storage is not configured.")
    st.stop()

main(
    repository=CloudAcademicRepository(url, key, token),
    storage_caption="Shared demo workspace. Saved changes remain after you leave.",
)
