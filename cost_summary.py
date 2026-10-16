from tokenomics_logger import logged_orchestrator, run_traced_query

QUESTIONS = [
    "How many active projects do we have?",
    "What is the total invoiced amount for each client?",
    "Which consultants work on the Beta Risk Dashboard project?",
    "What is our onboarding process?",
    "What is our expense policy for travel?",
    "What are the main phases of a cloud migration?",
    "How many active projects do we have, and what's our onboarding process?",
    "Which invoices are overdue, and what is our policy for overdue invoices?",
    "How many consultants are Managers, and what is the billable hours target for a Manager?",
    "What's the weather like today?",
]

rows = []
totals = {"sql_agent": 0, "retrieval_agent": 0, "synthesis": 0}
total_cost = 0.0

for i, q in enumerate(QUESTIONS, 1):
    print(f"\n----- Query {i}/{len(QUESTIONS)}: {q}")
    r = run_traced_query(logged_orchestrator, q)
    t = r["token_usage_by_component"]
    for comp in totals:
        totals[comp] += t[comp]["input"] + t[comp]["output"]
    total_cost += r["cost_breakdown"]["total_cost"]
    rows.append((i, r["route"], t, r["cost_breakdown"]["total_cost"], q))

print("\n\n" + "=" * 100)
print("10-QUERY COST SUMMARY")
print("=" * 100)
print(f"{'#':<3} {'route':<10} {'SQL agent':>12} {'Retrieval':>12} {'Synthesis':>12} {'USD':>10}  question")
for i, route, t, usd, q in rows:
    cells = [f"{t[c]['input'] + t[c]['output']:>12,}" for c in ("sql_agent", "retrieval_agent", "synthesis")]
    print(f"{i:<3} {route:<10} {' '.join(cells)} {usd:>10.5f}  {q[:45]}")
print("-" * 100)
grand = sum(totals.values())
print(f"{'':<3} {'TOTAL':<10} {totals['sql_agent']:>12,} {totals['retrieval_agent']:>12,} "
      f"{totals['synthesis']:>12,} {total_cost:>10.5f}")
print()
for comp, n in sorted(totals.items(), key=lambda x: -x[1]):
    print(f"  {comp:<16} {n:>8,} tokens  ({n / grand:.0%} of all tokens)")
top = max(totals, key=totals.get)
print(f"\nComponent that consumed the most tokens: {top}")
print(f"Total cost for {len(QUESTIONS)} queries: ${total_cost:.4f}  "
      f"(average ${total_cost / len(QUESTIONS):.5f} per query, ~${total_cost / len(QUESTIONS) * 1000:.2f} per 1,000 queries)")