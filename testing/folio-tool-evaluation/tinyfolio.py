import streamlit as st
from datetime import date

st.title("Folio Prototype")

if "assignments" not in st.session_state:
   st.session_state.assignments = []

name = st.text_input("Assignment Name")

due_date = st.date_input("Due Date", value=date.today())

priority = st.selectbox (
   "Priority",
   ["Low", "Medium", "High"]
)

if st.button("Add Assignment"):
   if not name.strip():
      st.error("Assignment name is required.")
   else:
      st.session_state.assignments.append(
            {
               "Assignment": name,
               "Due Date": due_date,
               "Priority": priority,
            }
      )
      st.success("Assignment added.")

st.subheader("Assignments")

if st.session_state.assignments:
   st.table(st.session_state.assignments)
else:
   st.write("No assignments added.")