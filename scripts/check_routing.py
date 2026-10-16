import json
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import questions
from orchestrator import run_orchestrator

cases = [("SQL-only", questions.SQL_ONLY),
         ("Retrieval-only", questions.DOCS_ONLY),
         ("Both (multi-tool)", questions.BOTH)]

lines = ["# Step 4 evidence: orchestrator routing", ""]
for label, q in cases:
    print(f"\n--- {label}: {q}")
    s = run_orchestrator(q)
    block = {
        "question": q,
        "route": s.get("route"),
        "sql_agent_ran": s.get("sql_result") is not None,
        "retrieval_agent_ran": s.get("retrieval_result") is not None,
        "sql_result": s.get("sql_result"),
        "retrieval_result": s.get("retrieval_result"),
        "final_answer": s.get("final_answer"),
    }
    text = json.dumps(block, indent=2, default=str)
    print(text)
    lines += [f"## {label}", "", "```json", text, "```", ""]

path = os.path.join(ROOT, "evidence", "step4_routing.md")
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nSaved {path}")