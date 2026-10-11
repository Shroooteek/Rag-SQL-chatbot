"""
Legacy (Excel/CSV) backend
===========================
Loads an uploaded Excel or CSV file into a throwaway SQLite database, then
uses a LangGraph SQL agent (via OpenRouter) to answer natural-language
questions about the data.
"""

import os
import sqlite3
import tempfile

import pandas as pd
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CHAT_MODEL = "google/gemini-2.5-flash"
TABLE_NAME = "uploaded_data"


def _require_api_key() -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY in a .env file "
            "in the same folder as app.py, then restart Streamlit."
        )
    return OPENROUTER_API_KEY


def _load_dataframe(file_path: str) -> pd.DataFrame:
    if file_path.lower().endswith(".csv"):
        return pd.read_csv(file_path)
    return pd.read_excel(file_path)


def build_sql_agent_from_excel(file_path: str, table_name: str = TABLE_NAME):
    df = _load_dataframe(file_path)

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    conn = sqlite3.connect(db_path)
    df.to_sql(table_name, conn, index=False, if_exists="replace")
    conn.close()

    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0,
        max_tokens=1024,
        api_key=_require_api_key(),
        base_url=OPENROUTER_BASE_URL,
    )
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    system_message = f"""
You are an agent designed to interact with a SQL database.
The file the user uploaded has been loaded into a single table called "{table_name}".

Given an input question, create a syntactically correct {db.dialect} query,
run it, then look at the results and return the answer in plain language.

Unless the user specifies a number of examples, limit results to at most 10.
Never select all columns - only the ones relevant to the question.
Always inspect the schema of "{table_name}" before writing a query.
You MUST double check your query before executing it, and rewrite it if it errors.
Never run INSERT, UPDATE, DELETE, DROP or any other statement that modifies data.
"""

    agent = create_react_agent(llm, tools, prompt=system_message)
    return agent, db_path


def query_excel_agent(agent, user_query: str) -> str:
    final_message = None
    for step in agent.stream(
        {"messages": [{"role": "user", "content": user_query}]},
        stream_mode="values",
    ):
        final_message = step["messages"][-1]

    if final_message is None:
        return "No answer produced."
    return final_message.content
