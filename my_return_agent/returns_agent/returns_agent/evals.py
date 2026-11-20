"""Tests the agent on the 10 questions in golden_dataset.py.

    python evals.py v1      test prompt v1
    python evals.py v2      test prompt v2   (the default)
"""

import sys

import database
from agent import build_agent
from golden_dataset import TESTS

version = sys.argv[1] if len(sys.argv) > 1 else "v2"     # python evals.py v1  ->  "v1"
agent = build_agent(version)
score = 0

for number, (customer, question, expected) in enumerate(TESTS, start=1):
    database.reset()           # fresh data for every test

    # 1. Ask the agent
    agent.invoke(
        {"messages": [("user", question)]},
        {"configurable": {"thread_id": f"test-{number}"}},     # each test is its own conversation
        context={"customer_id": customer},
    )

    # 2. See what it booked
    booked = "nothing"
    for order in database.get_customer_orders(customer):
        if order["return_type"]:
            booked = f"{order['order_id']} {order['return_type']} {order['return_status']}"

    # 3. Compare with the expected answer
    if booked == expected:
        score += 1
        print(f"PASS  test {number}: {question}")
    else:
        print(f"FAIL  test {number}: {question}  | expected: {expected} | got: {booked}")

print(f"\n{version} score: {score}/{len(TESTS)}")