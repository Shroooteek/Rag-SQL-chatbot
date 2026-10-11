"""
Quick latency benchmark for your RAG chatbot's answer function.

HOW TO USE:
1. Put a sample PDF in this folder (or point PDF_PATH at one you already have).
2. Fill in TEST_QUERIES below with ~8-10 realistic questions someone would
   actually ask your RAG bot, based on that PDF's content.
3. Run: python timing_test.py
4. Use the "Average latency" number it prints as your resume metric.

This calls rag_backend.py directly (build_vectorstore_from_pdf once, then
answer_from_pdf per query) - the same functions app.py uses - so timings
reflect the real embedding + LLM round trip through OpenRouter.
"""

import time
import statistics

from rag_backend import build_vectorstore_from_pdf, answer_from_pdf

PDF_PATH = "C:\Users\shrut\Downloads\Careers _ Dalberg.pdf"  # change to the path of a PDF you want to test against

TEST_QUERIES = [
    # Replace these with real questions relevant to your indexed PDF
    "What is dalberg?",
    "Summarize the key terms.",
    "What is the assignment?",
    "How will the assignment be assessed?",
    "Tell me about dalbergs clients?",
]


def run_benchmark():
    print(f"Indexing '{PDF_PATH}'...")
    setup_start = time.perf_counter()
    vector_store = build_vectorstore_from_pdf(PDF_PATH)
    setup_elapsed = time.perf_counter() - setup_start
    print(f"Indexing took {setup_elapsed:.2f}s\n")

    latencies = []
    for i, query in enumerate(TEST_QUERIES, start=1):
        start = time.perf_counter()
        try:
            answer = answer_from_pdf(vector_store, query)
        except Exception as e:
            print(f"Query {i} failed: {e}")
            continue
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)
        print(f"Query {i}: {elapsed:.2f}s  ->  {query[:60]}")

    print("\n--- Results ---")
    if latencies:
        print(f"Queries run:      {len(latencies)}")
        print(f"Average latency:  {statistics.mean(latencies):.2f}s")
        print(f"Median latency:   {statistics.median(latencies):.2f}s")
        print(f"Min / Max:        {min(latencies):.2f}s / {max(latencies):.2f}s")
    else:
        print("No successful queries recorded - check the errors above.")


if __name__ == "__main__":
    run_benchmark()