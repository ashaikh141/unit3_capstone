from agents.retrieval_agent import run_retrieval_agent
from agents.sql_agent import run_sql_agent

TOOL_REGISTRY = {
    "sql_agent": {
        "function": run_sql_agent,
        "schema": {
            "name": "sql_agent",
            "description": (
                "Query the firm's relational database for structured data about clients, projects, "
                "consultants, and invoices. Use for counts, totals, averages, lists, statuses, dates, "
                "budgets, contract values, billable hours, and invoice amounts, e.g. 'How many active "
                "projects do we have?' or 'Which invoices are overdue?'. "
                "NOT for policies, processes, guidelines, or rules (how things should be done); "
                "use retrieval_agent for those."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
    "retrieval_agent": {
        "function": run_retrieval_agent,
        "schema": {
            "name": "retrieval_agent",
            "description": (
                "Search the firm's documents for policies, procedures, and written guidance: onboarding, "
                "invoicing and payment rules, project delivery methodology, consultant grades and "
                "utilization targets, expenses and travel, remote work and data security, plus a cloud "
                "migration playbook, a Q2 2026 client report, and a retail supply chain case study. "
                "Use for 'what is our process/policy/rule' questions, e.g. 'What is our onboarding "
                "process?'. "
                "NOT for live figures about specific clients, projects, consultants, or invoices "
                "(counts, totals, statuses); use sql_agent for those."
            ),
            "input_schema": {
                "type": "object",
                "properties": {"question": {"type": "string"}},
                "required": ["question"],
            },
        },
    },
}


def get_all_schemas() -> list:
    return [tool["schema"] for tool in TOOL_REGISTRY.values()]


def call_tool(tool_name: str, question: str) -> dict:
    if tool_name not in TOOL_REGISTRY:
        return {
            "success": False,
            "answer": f"Unknown tool: {tool_name}",
            "sources": [],
            "metadata": {"error": f"Unknown tool: {tool_name}",
                         "available_tools": list(TOOL_REGISTRY)},
        }
    try:
        return TOOL_REGISTRY[tool_name]["function"](question)
    except Exception as e:
        return {
            "success": False,
            "answer": f"The {tool_name} tool failed: {e}",
            "sources": [],
            "metadata": {"error": str(e)},
        }