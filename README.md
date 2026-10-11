# AI Chatbot: Chat with Your PDFs and Spreadsheets

A Streamlit app that lets you ask questions about your own documents in plain English. Pick a mode, upload a file, and start chatting.

- **RAG (PDF) mode:** upload a PDF and ask questions about its content. Answers come only from the document.
- **Legacy (Excel/CSV) mode:** upload a spreadsheet and ask questions about the data. An AI agent writes and runs SQL for you and explains the result.

All model calls (chat and embeddings) go through [OpenRouter](https://openrouter.ai/).

## Features

- Two modes in one app, switchable from the sidebar
- Built-in chat interface with conversation history and a reset button
- PDF answers grounded strictly in retrieved context, with an "I don't know" fallback instead of guessing
- Natural-language questions over Excel/CSV data, using a read-only SQL agent
- Nothing is saved permanently: the vector store lives in memory and the spreadsheet goes into a temporary SQLite database
- Latency benchmark scripts for both modes

## How It Works

### RAG mode (`rag_backend.py`)
1. The PDF is loaded with `PyPDFLoader`.
2. Text is split into chunks of 1,000 characters with 200 characters of overlap.
3. Chunks are embedded with `google/gemini-embedding-2` and stored in an in-memory Chroma vector store.
4. For each question, the 5 most similar chunks are retrieved.
5. `google/gemini-2.5-flash` answers using only those chunks.

### Legacy mode (`excel_backend.py`)
1. The Excel/CSV file is read with pandas and written to a temporary SQLite table.
2. A LangGraph ReAct agent with the SQL database toolkit inspects the schema, writes a query, runs it, and summarizes the result.
3. The agent is instructed to run read-only queries only (no INSERT, UPDATE, DELETE or DROP).

## Project Structure

```
.
├── app.py                # Streamlit UI (sidebar, chat, session state)
├── rag_backend.py        # PDF -> chunks -> embeddings -> Chroma -> answer
├── excel_backend.py      # Excel/CSV -> SQLite -> LangGraph SQL agent
├── timing_test.py        # Latency benchmark for RAG mode
├── timing_test_excel.py  # Latency benchmark for Legacy mode
└── requirements.txt
```

## Setup

**1. Install dependencies**

```bash
pip install -r requirements.txt
```

**2. Add your OpenRouter API key**

Create a file named `.env` in the project folder:

```
OPENROUTER_API_KEY=your_key_here
```

Get a key at [openrouter.ai/keys](https://openrouter.ai/keys). Never commit `.env` to Git. Add it to your `.gitignore`.

**3. Run the app**

```bash
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## Usage

1. Choose **RAG (PDF)** or **Legacy (Excel/CSV)** in the sidebar.
2. Upload a file.
3. Ask questions in the chat box.

Example questions:

| Mode | Example |
|------|---------|
| RAG | "Summarize the key terms." / "How will the assignment be assessed?" |
| Legacy | "What's the average monthly income of employees in Sales?" / "How many married employees earn more than $10,000 a month?" |

Switching modes clears the chat and the loaded file.

## Benchmarking Latency

Both scripts index or load a file once, run a list of sample questions, and print average, median, min and max response times.

```bash
python timing_test.py          # RAG mode
python timing_test_excel.py    # Legacy mode
```

Edit `PDF_PATH` / `EXCEL_PATH` and `TEST_QUERIES` at the top of each script first. On Windows, use raw strings for paths, e.g. `r"C:\Users\you\Downloads\file.pdf"`.

## Tech Stack

- [Streamlit](https://streamlit.io/): UI
- [LangChain](https://www.langchain.com/) and [LangGraph](https://www.langchain.com/langgraph): retrieval and agent orchestration
- [Chroma](https://www.trychroma.com/): vector store
- [OpenRouter](https://openrouter.ai/): Gemini 2.5 Flash for chat, Gemini Embedding 2 for embeddings
- pandas and SQLite: spreadsheet loading and querying
- pypdf: PDF parsing

## Notes and Limitations

- Scanned PDFs without a text layer won't work, since there is no OCR step.
- Legacy mode loads the whole file into a single table named `uploaded_data`.
- Answers depend on the underlying model and can be wrong. Double-check anything important.
