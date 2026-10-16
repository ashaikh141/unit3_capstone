from tools import run_retrieval_agent, run_sql_agent

TOOL_REGISTRY = {
    "sql_agent": {
        "function": run_sql_agent,
        "description": (
            "Answers questions about STRUCTURED records in the company database: "
            "clients (name, industry, region, contract value), projects (status, dates, budget), "
            "consultants (grade, specialisation, billable hours, project), and invoices "
            "(amount, status, due date, paid date). Use it for counts, totals, sums, averages, "
            "statuses, dates, amounts, rankings, and who is assigned to what. "
            "NOT for policies, processes, guidelines, or anything written in company documents."
        ),
    },
    "retrieval_agent": {
        "function": run_retrieval_agent,
        "description": (
            "Answers questions from the firm's WRITTEN policy documents: onboarding, "
            "invoicing and payment policy, project delivery process, and other guidelines. "
            "NOT for counting or totaling records, looking up specific clients, projects, "
            "invoices, or consultants, or any number stored in the database."
        ),
    },
}


def describe_tools():
    return "\n".join(f"- {name}: {spec['description']}" for name, spec in TOOL_REGISTRY.items())