import json
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import questions
from orchestrator import run_orchestrator

EVIDENCE = os.path.join(ROOT, "evidence")
os.makedirs(EVIDENCE, exist_ok=True)


def one_line(text, n=220):
    return " ".join(str(text or "").split()).replace("|", "/")[:n]


def auto_check(qtype, s):
    sql = s.get("sql_result") or {}
    ret = s.get("retrieval_result") or {}
    validation = (sql.get("metadata") or {}).get("sql_validation")
    if qtype == "rds":
        return "PASS" if s["route"] == "sql" and sql.get("success") else "CHECK"
    if qtype == "docs":
        return "PASS" if s["route"] == "retrieval" and ret.get("success") else "CHECK"
    if qtype == "both":
        return "PASS" if s["route"] == "both" and sql.get("success") and ret.get("success") else "CHECK"
    if qtype == "unsafe":
        return "PASS (blocked)" if validation == "BLOCKED" else "CHECK"
    if qtype == "unanswerable":
        return "PASS (declined)" if s["route"] == "none" or not (sql.get("success") or ret.get("success")) else "CHECK"
    return "-"


all_questions = questions.TEST_SUITE + questions.EXTRA_FOR_COST
results = []
for i, (qtype, q) in enumerate(all_questions, 1):
    print(f"\n[{i}/{len(all_questions)}] ({qtype}) {q}")
    s = run_orchestrator(q)
    sql = s.get("sql_result") or {}
    total = s["token_usage"]["total"]
    rec = {
        "n": i, "type": qtype, "question": q, "route": s.get("route"),
        "sql_validation": (sql.get("metadata") or {}).get("sql_validation", "N/A (SQL agent not used)"),
        "sql": (sql.get("metadata") or {}).get("sql", ""),
        "answer": s.get("final_answer"),
        "check": auto_check(qtype, s),
        "input_tokens": total["input_tokens"], "output_tokens": total["output_tokens"],
        "cost_usd": total["cost_usd"], "by_component": s["token_usage"]["by_component"],
    }
    results.append(rec)
    print(f"   route={rec['route']}  validation={rec['sql_validation']}  check={rec['check']}  cost=${rec['cost_usd']:.6f}")

with open(os.path.join(EVIDENCE, "test_suite_raw.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, default=str)

suite = results[:len(questions.TEST_SUITE)]
md = ["# Step 7 evidence: 8-question test suite", "",
      "| # | Type | Question | Route | SQL validation | Result |",
      "|---|---|---|---|---|---|"]
for r in suite:
    md.append(f"| {r['n']} | {r['type']} | {one_line(r['question'], 120)} | {r['route']} | {r['sql_validation']} | {r['check']} |")
md += ["", "## Full answers", ""]
for r in suite:
    md += [f"### {r['n']}. ({r['type']}) {r['question']}", "",
           f"- **Route:** {r['route']}",
           f"- **SQL validation:** {r['sql_validation']}",
           f"- **SQL:** `{one_line(r['sql'], 400)}`" if r["sql"] else "- **SQL:** none",
           "", "**Answer:**", "", str(r["answer"]), ""]
with open(os.path.join(EVIDENCE, "step7_test_suite.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(md))

by_comp = {}
for r in results:
    for comp, v in r["by_component"].items():
        b = by_comp.setdefault(comp, {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        for k in ("calls", "input_tokens", "output_tokens"):
            b[k] += v[k]
        b["cost_usd"] += v["cost_usd"]
tot_in = sum(r["input_tokens"] for r in results)
tot_out = sum(r["output_tokens"] for r in results)
tot_cost = sum(r["cost_usd"] for r in results)
ranked = sorted(by_comp.items(), key=lambda kv: kv[1]["input_tokens"] + kv[1]["output_tokens"], reverse=True)
top_name, top = ranked[0]
top_tokens = top["input_tokens"] + top["output_tokens"]

cs = [f"# Step 6 evidence: cost summary ({len(results)} queries through the full orchestrator)", "",
      "Rates: Claude Sonnet 4.6, US geo cross-region inference, $3.30 per 1M input tokens, $16.50 per 1M output tokens (Amazon Bedrock pricing page).", "",
      "| # | Question | Route | Input tokens | Output tokens | Cost (USD) |",
      "|---|---|---|---|---|---|"]
for r in results:
    cs.append(f"| {r['n']} | {one_line(r['question'], 90)} | {r['route']} | {r['input_tokens']} | {r['output_tokens']} | ${r['cost_usd']:.6f} |")
cs.append(f"| **Total** | | | **{tot_in}** | **{tot_out}** | **${tot_cost:.6f}** |")
cs += ["", "## By component", "",
       "| Component | Calls | Input tokens | Output tokens | Cost (USD) | Share of tokens |",
       "|---|---|---|---|---|---|"]
for name, v in ranked:
    share = (v["input_tokens"] + v["output_tokens"]) / max(tot_in + tot_out, 1) * 100
    cs.append(f"| {name} | {v['calls']} | {v['input_tokens']} | {v['output_tokens']} | ${v['cost_usd']:.6f} | {share:.1f}% |")
cs += ["", f"**Total cost for {len(results)} queries:** ${tot_cost:.6f} "
           f"(average ${tot_cost / len(results):.6f} per query)",
       f"**Component that consumed the most tokens:** {top_name} "
       f"({top_tokens} tokens, {top_tokens / max(tot_in + tot_out, 1) * 100:.1f}% of all tokens)"]
with open(os.path.join(EVIDENCE, "step6_cost_summary.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(cs))

print("\nSaved evidence/step7_test_suite.md, evidence/step6_cost_summary.md, evidence/test_suite_raw.json")