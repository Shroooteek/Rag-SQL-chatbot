"""
RAG backend
===========
Loads a PDF, chunks it, embeds the chunks via OpenRouter (Gemini Embedding 2),
stores them in an in-memory Chroma vector store, and answers questions using
only the retrieved PDF context. All model calls go through OpenRouter.
"""

import os

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

CHAT_MODEL = "google/gemini-2.5-flash"
EMBEDDING_MODEL = "google/gemini-embedding-2"


def _require_api_key() -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY in a .env file "
            "in the same folder as app.py, then restart Streamlit."
        )
    return OPENROUTER_API_KEY


def build_vectorstore_from_pdf(pdf_path: str) -> Chroma:
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    if not docs:
        raise ValueError("The PDF could not be loaded or contains no text.")

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    if not chunks:
        raise ValueError("No text chunks were created from the PDF.")

    embedding_model = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=_require_api_key(),
        base_url=OPENROUTER_BASE_URL,
        check_embedding_ctx_length=False,
    )

    vector_store = Chroma.from_documents(documents=chunks, embedding=embedding_model)
    return vector_store


def answer_from_pdf(vector_store: Chroma, query: str, k: int = 5) -> str:
    retrieved_docs = vector_store.similarity_search(query, k=k)

    if not retrieved_docs:
        return "I don't know based on the uploaded PDF."

    context = "\n\n".join(doc.page_content for doc in retrieved_docs)

    prompt = f"""You are a PDF question-answering assistant.

Answer the question using ONLY the information contained in the context below.

Rules:
1. Do not use outside knowledge.
2. Do not make up information.
3. If the answer is not present in the context, say "I don't know based on the uploaded PDF."
4. Keep the answer clear and relevant.

PDF CONTEXT:
------------------------------
{context}
------------------------------

QUESTION:
{query}

ANSWER:
"""

    llm = ChatOpenAI(
        model=CHAT_MODEL,
        temperature=0.3,
        max_tokens=1024,
        api_key=_require_api_key(),
        base_url=OPENROUTER_BASE_URL,
    )

    response = llm.invoke(prompt)
    return response.content
