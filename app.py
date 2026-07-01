import streamlit as st
from ai_agent import ask, list_available_layouts

# ---------- Page Setup ----------
st.set_page_config(
    page_title="FileMaker AI Assistant",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 FileMaker AI Assistant")
st.write(
    "Ask any question about your FileMaker data in plain English. "
    "The assistant will figure out which table to look in and fetch the answer for you."
)

# ---------- Sidebar: show available tables ----------
# This calls our list_available_layouts() function so the user can see
# what tables exist, without needing to ask the AI first.
with st.sidebar:
    st.header("Available Tables")
    if st.button("Refresh table list"):
        st.session_state.pop("layouts", None)

    if "layouts" not in st.session_state:
        try:
            with st.spinner("Loading tables from FileMaker..."):
                st.session_state["layouts"] = list_available_layouts()
        except Exception as e:
            st.session_state["layouts"] = []
            st.error(f"Could not load tables: {e}")

    if st.session_state["layouts"]:
        for layout in st.session_state["layouts"]:
            st.write(f"• {layout}")
    else:
        st.write("No tables found, or connection failed.")

# ---------- Keep chat history so the conversation stays visible ----------
if "history" not in st.session_state:
    st.session_state["history"] = []  # list of (question, answer) tuples

# Show previous Q&A pairs
for question, answer in st.session_state["history"]:
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.write(answer)

# ---------- Input box ----------
user_question = st.chat_input("Type your question here...")

if user_question:
    with st.chat_message("user"):
        st.write(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = ask(user_question)
            except Exception as e:
                answer = f"Something went wrong: {e}"
        st.write(answer)

    st.session_state["history"].append((user_question, answer))