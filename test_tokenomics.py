import json

from tokenomics_logger import LOG_PATH, logged_orchestrator, run_traced_query

question = "How many active projects do we have, and what's our onboarding process?"

print("#" * 80)
print("PART 2: trace a 'both' question")
print("#" * 80)
result = run_traced_query(logged_orchestrator, question)
trace_id = result["trace_id"]

print("\n" + "#" * 80)
print(f"PART 2 CHECK: rebuild the decision chain for trace {trace_id} from {LOG_PATH} alone")
print("#" * 80)
with open(LOG_PATH) as f:
    for line in f:
        entry = json.loads(line)
        if entry["trace_id"] == trace_id:
            print(f"{entry['timestamp']}  {entry['stage']:<16} {json.dumps(entry['details'], default=str)[:150]}")

print("\n" + "#" * 80)
print("PART 3 ACTIVITY: break down this query's cost")
print("#" * 80)
for component, t in result["token_usage_by_component"].items():
    print(f"  {component:<16} {t['input']:>6} in  {t['output']:>5} out")
print(json.dumps(result["cost_breakdown"], indent=2))