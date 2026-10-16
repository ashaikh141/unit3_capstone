import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import run_sql_agent, run_retrieval_agent

EXPECTED = ["answer", "metadata", "sources", "success"]
cases = [
    ("run_sql_agent", run_sql_agent, "How many projects are there?"),
    ("run_retrieval_agent", run_retrieval_agent, "What is our onboarding process?"),
]

print("=== Step 2: Standardized tool interface ===\n")
for name, fn, question in cases:
    r = fn(question)
    keys = sorted(r.keys())
    print(f"{name}(\"{question}\")")
    print(f"  top-level keys: {keys}   {'PASS' if keys == EXPECTED else 'FAIL'}")
    print(f"  success:  {r['success']}")
    print(f"  answer:   {r['answer'][:250]}")
    print(f"  sources:  {r['sources']}")
    print(f"  metadata: {json.dumps(r['metadata'], default=str)[:400]}\n")