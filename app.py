"""
#AI Chatbot - Streamlit UI
=========================
Two modes, picked from the sidebar:
  - RAG mode:    upload a PDF, ask questions about its content.
  - Legacy mode: upload an Excel/CSV file, ask questions about the data.

Run with:
    streamlit run app.py
"""

import os
import tempfile

import streamlit as st
from dotenv import load_dotenv

from rag_backend import build_vectorstore_from_pdf, answer_from_pdf
from excel_backend import build_sql_agent_from_excel, query_excel_agent

load_dotenv()

st.set_page_config(page_title="AI Chatbot", page_icon="🤖", layout="centered")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "mode": None,
    "messages": [],
    "vector_store": None,
    "sql_agent": None,
    "file_ready": False,
    "loaded_file_name": None,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

st.title("🤖 AI Chatbot")

# ---------------------------------------------------------------------------
# Sidebar: mode selection + file upload
# ---------------------------------------------------------------------------
MODE_LABELS = {"rag": "RAG (PDF)", "legacy": "Legacy (Excel/CSV)"}

with st.sidebar:
    st.header("Settings")

    label_to_mode = {v: k for k, v in MODE_LABELS.items()}
    current_label = MODE_LABELS.get(st.session_state.mode)
    chosen_label = st.radio(
        "Choose chatbot mode",
        list(MODE_LABELS.values()),
        index=list(MODE_LABELS.values()).index(current_label) if current_label else None,
    )
    new_mode = label_to_mode.get(chosen_label)

    if new_mode != st.session_state.mode:
        st.session_state.mode = new_mode
        st.session_state.messages = []
        st.session_state.vector_store = None
        st.session_state.sql_agent = None
        st.session_state.file_ready = False
        st.session_state.loaded_file_name = None

    if st.session_state.mode == "rag":
        uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])
        if uploaded_file is not None and uploaded_file.name != st.session_state.loaded_file_name:
            with st.spinner("Reading PDF and building the index..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                try:
                    st.session_state.vector_store = build_vectorstore_from_pdf(tmp_path)
                    st.session_state.file_ready = True
                    st.session_state.loaded_file_name = uploaded_file.name
                    st.session_state.messages = []
                except Exception as exc:  # noqa: BLE001
                    st.session_state.file_ready = False
                    st.error(f"Couldn't process that PDF: {exc}")
            if st.session_state.file_ready:
                st.success(f"'{uploaded_file.name}' indexed. Ask away!")

    elif st.session_state.mode == "legacy":
        uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None and uploaded_file.name != st.session_state.loaded_file_name:
            with st.spinner("Loading data..."):
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name
                try:
                    agent, _db_path = build_sql_agent_from_excel(tmp_path)
                    st.session_state.sql_agent = agent
                    st.session_state.file_ready = True
                    st.session_state.loaded_file_name = uploaded_file.name
                    st.session_state.messages = []
                except Exception as exc:  # noqa: BLE001
                    st.session_state.file_ready = False
                    st.error(f"Couldn't load that file: {exc}")
            if st.session_state.file_ready:
                st.success(f"'{uploaded_file.name}' loaded. Ask away!")

    if st.session_state.messages and st.button("Reset conversation"):
        st.session_state.messages = []
        st.rerun()

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------
if st.session_state.mode is None:
    st.info("👈 Pick a mode in the sidebar to get started: **RAG** for PDFs, or **Legacy** for Excel/CSV data.")
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not st.session_state.file_ready:
        file_kind = "PDF" if st.session_state.mode == "rag" else "Excel/CSV file"
        st.warning(f"Upload a {file_kind} in the sidebar first.")
    else:
        user_query = st.chat_input("Type your question here...")
        if user_query:
            st.session_state.messages.append({"role": "user", "content": user_query})
            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        if st.session_state.mode == "rag":
                            answer = answer_from_pdf(st.session_state.vector_store, user_query)
                        else:
                            answer = query_excel_agent(st.session_state.sql_agent, user_query)
                    except Exception as exc:  # noqa: BLE001
                        answer = f"⚠️ Error: {exc}"
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
