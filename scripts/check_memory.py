import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import questions
from conversation import MAX_ANSWER_CHARS, MAX_HISTORY_TURNS
from orchestrator import run_orchestrator


def sql_of(state):
    return ((state.get("sql_result") or {}).get("metadata") or {}).get("sql", "(no SQL)")


t1 = run_orchestrator(questions.FOLLOWUP_TURN_1)
t2 = run_orchestrator(questions.FOLLOWUP_TURN_2, t1["history"])
no_mem = run_orchestrator(questions.FOLLOWUP_TURN_2)

in1 = t1["token_usage"]["total"]["input_tokens"]
in2 = t2["token_usage"]["total"]["input_tokens"]
in_nm = no_mem["token_usage"]["total"]["input_tokens"]

md = [
    "# Silver evidence: conversation memory (local)", "",
    f"History cap: {MAX_HISTORY_TURNS} turns, each replayed answer truncated to {MAX_ANSWER_CHARS} characters.", "",
    f"## Turn 1: {questions.FOLLOWUP_TURN_1}", "", f"- Route: {t1['route']}", f"- SQL: `{sql_of(t1)}`",
    f"- Input tokens: {in1}", "", t1["final_answer"], "",
    f"## Turn 2 (with history): {questions.FOLLOWUP_TURN_2}", "", f"- Route: {t2['route']}", f"- SQL: `{sql_of(t2)}`",
    f"- Input tokens: {in2}", "", t2["final_answer"], "",
    "## Same follow-up WITHOUT history (for comparison)", "", f"- SQL: `{sql_of(no_mem)}`",
    f"- Input tokens: {in_nm}", "", no_mem["final_answer"], "",
    "## Cost impact", "",
    f"- Turn 2 with history used {in2} input tokens vs {in_nm} without history.",
    f"- Memory added {in2 - in_nm} input tokens ({(in2 - in_nm) / max(in_nm, 1) * 100:.1f}% more) for one replayed turn.",
]
path = os.path.join(ROOT, "evidence", "silver_memory_local.md")
with open(path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("\n".join(md))
print(f"\nSaved {path}")