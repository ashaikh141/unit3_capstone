from bedrock_client import invoke_claude
from tool_registry import TOOL_REGISTRY, get_all_schemas


def suggest_tool(question: str) -> str:
    schemas_description = "\n".join(f"- {s['name']}: {s['description']}" for s in get_all_schemas())
    prompt = (
        f"Available tools:\n{schemas_description}\n\n"
        f"Question: {question}\n\n"
        "Which tool should handle this? Reply with only the tool name."
    )
    result = invoke_claude(prompt, max_tokens=20)
    return result["text"].strip()


QUESTIONS = [
    "How many consultants do we have on active projects?",
    "What is our expense reimbursement policy?",
    "How many active projects do we have and what's our onboarding process?",
]

for q in QUESTIONS:
    suggestion = suggest_tool(q)
    valid = "valid tool" if suggestion in TOOL_REGISTRY else "NOT a registered tool name"
    print(f"Q: {q}")
    print(f"Suggested tool: {suggestion}  ({valid})\n")