"""
Quick latency benchmark for your Excel/CSV chatbot's answer function.

HOW TO USE:
1. Point EXCEL_PATH at the Excel/CSV file you want to test against.
2. Fill in TEST_QUERIES below with real questions relevant to that file's data.
3. Run: python timing_test_excel.py
4. Use the "Average latency" number it prints as your resume metric.

This calls excel_backend.py directly (build_sql_agent_from_excel once, then
query_excel_agent per query) - the same functions app.py uses - so timings
reflect the real SQL-agent + LLM round trip through OpenRouter.
"""

import time
import statistics

from excel_backend import build_sql_agent_from_excel, query_excel_agent

EXCEL_PATH = r"C:\Users\shrut\Downloads\HR-Em.csv"

TEST_QUERIES = [
    "People working in life sciences that are single",
    "What's the average monthly income of employees in Sales?",
    "How many married employees earn more than $10,000 a month?",
    "How many employees who travel frequently are also single?",
    "What department and job role does the 100th employee in the list work in?",
    "How would you label the salary tier of the employee in row 10 - Low under $3,000, Medium up to $7,000, High above that?",
]


def run_benchmark():
    print(f"Loading '{EXCEL_PATH}' into a SQL agent...")
    setup_start = time.perf_counter()
    agent, db_path = build_sql_agent_from_excel(EXCEL_PATH)
    setup_elapsed = time.perf_counter() - setup_start
    print(f"Setup took {setup_elapsed:.2f}s\n")

    latencies = []
    for i, query in enumerate(TEST_QUERIES, start=1):
        start = time.perf_counter()
        try:
            answer = query_excel_agent(agent, query)
        except Exception as e:
            print(f"Query {i} failed: {e}")
            continue
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)
        print(f"Query {i}: {elapsed:.2f}s  ->  {query[:60]}")
        print(f"   Answer: {answer[:200]}\n")

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