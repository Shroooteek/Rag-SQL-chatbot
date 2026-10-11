# AI Chatbot (Streamlit, PDF or Excel/CSV)

## What changed
- The React/Node front end (`frontend_react.js`, `package.json`) is gone. The whole UI is now
  one Streamlit app (`app.py`) using Streamlit's built-in chat components (`st.chat_message`,
  `st.chat_input`) — no separate frontend server, no JS build step.
- The old FastAPI backend, LangGraph router, and one-off scripts (`fastapipratice.py`,
  `graphh.py`, `graphh1.py`, `new.py`, `new2.py`, `test.py`, `read_databse_postgres.py`,
  `dbutlis.py`) are replaced by two small, focused modules:
  - `rag_backend.py` — PDF upload → chunk → embed → Chroma vector store → retrieval-augmented answer.
  - `excel_backend.py` — Excel/CSV upload → loaded into a throwaway SQLite table → a
    LangGraph SQL agent (same idea as your old Postgres agent, just pointed at the file you
    upload instead of a live Postgres database).
- The sidebar lets you pick **RAG (PDF)** or **Legacy (Excel/CSV)** mode, upload the matching
  file, and chat. Switching modes clears the chat and the loaded file.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # then put your real GEMINI_API_KEY in .env
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## ⚠️ About your uploaded `_env` file
The `_env` file you uploaded has **live, plaintext API keys** in it (Gemini, Tavily, Groq,
Voyage, and a Postgres connection string with a password). I did not copy any of those keys
into the code — everything still reads from environment variables via `os.getenv(...)`. But
since that file has now passed through this chat, it's worth rotating those keys (especially
`GEMINI_API_KEY`/`GOOGLE_API_KEY` and the Postgres password) and keeping only a local `.env`
(never `_env` checked into anything) going forward.

## Notes
- RAG mode's vector store is rebuilt fresh per uploaded PDF and lives only for the session
  (no data persisted to disk), so re-uploading a different PDF won't mix content together.
- Legacy mode writes the uploaded spreadsheet into a temporary SQLite `.db` file, points the
  same kind of SQL agent your old code used at it, and won't run anything other than read-only
  queries (no INSERT/UPDATE/DELETE/DROP).
- Both modes need `GEMINI_API_KEY` set. Tavily/Groq/Postgres are no longer used by this app.
