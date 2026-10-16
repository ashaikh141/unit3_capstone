import tools

EXPECTED_KEYS = {"success", "answer", "sources", "metadata"}


def test_sql_tool_blocks_unsafe_sql_before_execution(monkeypatch):
    executed = []
    monkeypatch.setattr(tools.adapters, "get_schema_text", lambda: "TABLE invoices: id, amount")
    monkeypatch.setattr(tools.adapters, "run_select",
                        lambda sql, max_rows=200: executed.append(sql) or [])
    monkeypatch.setattr(tools.llm, "call_claude",
                        lambda component, system, user, max_tokens=800, temperature=0: "DELETE FROM invoices")

    r = tools.run_sql_agent("Delete all invoices")

    assert set(r) == EXPECTED_KEYS
    assert r["success"] is False
    assert r["metadata"]["sql_validation"] == "BLOCKED"
    assert executed == []


def test_sql_tool_runs_valid_sql(monkeypatch):
    monkeypatch.setattr(tools.adapters, "get_schema_text", lambda: "TABLE projects: id, status")
    monkeypatch.setattr(tools.adapters, "run_select", lambda sql, max_rows=200: [{"n": 3}])

    def fake_claude(component, system, user, max_tokens=800, temperature=0):
        return "SELECT COUNT(*) AS n FROM projects" if component == "sql_generation" else "There are 3 projects."
    monkeypatch.setattr(tools.llm, "call_claude", fake_claude)

    r = tools.run_sql_agent("How many projects?")
    assert set(r) == EXPECTED_KEYS
    assert r["success"] is True
    assert r["metadata"]["sql_validation"] == "PASSED"
    assert r["sources"] == ["SELECT COUNT(*) AS n FROM projects"]


def test_retrieval_tool_shape_and_grounding(monkeypatch):
    monkeypatch.setattr(tools.adapters, "retrieve_chunks",
                        lambda q, k=4: [{"doc": "onboarding.md", "text": "Week 1: training.", "score": 0.91}])
    monkeypatch.setattr(tools.llm, "call_claude",
                        lambda component, system, user, max_tokens=800, temperature=0:
                        "New hires complete training in week 1 [onboarding.md].")

    r = tools.run_retrieval_agent("What is onboarding?")
    assert set(r) == EXPECTED_KEYS
    assert r["success"] is True
    assert r["sources"] == ["onboarding.md"]
    assert r["metadata"]["grounded"] is True