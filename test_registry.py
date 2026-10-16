import json

from agents.retrieval_agent import run_retrieval_agent
from agents.sql_agent import run_sql_agent
from tool_registry import call_tool, get_all_schemas

print("#" * 80)
print("PART 1 CHECK: both agents return the same top-level keys")
print("#" * 80)
sql_result = run_sql_agent("How many active projects do we have?")
retrieval_result = run_retrieval_agent("What is our onboarding process?")
print("run_sql_agent keys:      ", list(sql_result.keys()))
print("run_retrieval_agent keys:", list(retrieval_result.keys()))
print("Identical:", list(sql_result.keys()) == list(retrieval_result.keys()))

print("\n" + "#" * 80)
print("PART 3: test the registry directly")
print("#" * 80)
print("Registered tools:", [s["name"] for s in get_all_schemas()])

for tool, question in [
    ("sql_agent", "How many active projects do we have?"),
    ("retrieval_agent", "What is our onboarding process?"),
    ("nonexistent_tool", "test"),
]:
    print("\n" + "=" * 80)
    print(f"call_tool('{tool}', '{question}')")
    print("-" * 80)
    print(json.dumps(call_tool(tool, question), indent=2, default=str))