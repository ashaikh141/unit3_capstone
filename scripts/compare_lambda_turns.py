import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ev = os.path.join(ROOT, "evidence")
r1 = json.load(open(os.path.join(ev, "response_turn1.json"), encoding="utf-8"))
r2 = json.load(open(os.path.join(ev, "response_turn2.json"), encoding="utf-8"))


def sql_of(r):
    return ((r.get("sql_result") or {}).get("metadata") or {}).get("sql", "(no SQL)")


in1 = r1["token_usage"]["total"]["input_tokens"]
in2 = r2["token_usage"]["total"]["input_tokens"]
md = [
    "# Silver evidence: conversation memory (deployed on Lambda)", "",
    f"## Turn 1: {r1['question']}", f"- SQL: `{sql_of(r1)}`", f"- Input tokens: {in1}", "", r1["answer"], "",
    f"## Turn 2: {r2['question']} (history passed from Turn 1 response)",
    f"- History sent: {len(r2.get('history', [])) - 1} prior turn(s)",
    f"- SQL: `{sql_of(r2)}`", f"- Input tokens: {in2}", "", r2["answer"], "",
    f"Turn 2 used {in2 - in1:+d} input tokens compared with Turn 1.",
]
out = os.path.join(ev, "silver_memory_lambda.md")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("\n".join(md))
print(f"\nSaved {out}")