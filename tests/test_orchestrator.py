import orchestrator
import registry
from conversation import MAX_HISTORY_TURNS


def _fake_tool(name):
    def fn(question, history=None):
        return {"success": True, "answer": f"{name} answer", "sources": [f"{name}-source"],
                "metadata": {"sql_validation": "PASSED"} if name == "sql" else {"grounded": True}}
    return fn


def _install_fakes(monkeypatch, route_reply):
    calls = []

    def fake_claude(component, system, user, max_tokens=800, temperature=0):
        calls.append(component)
        if component == "classification":
            return route_reply
        return "Combined answer [SQL Agent] [Retrieval Agent: retrieval-source]"

    monkeypatch.setattr(orchestrator.llm, "call_claude", fake_claude)
    monkeypatch.setitem(registry.TOOL_REGISTRY["sql_agent"], "function", _fake_tool("sql"))
    monkeypatch.setitem(registry.TOOL_REGISTRY["retrieval_agent"], "function", _fake_tool("retrieval"))
    return calls


def test_sql_only_route(monkeypatch):
    calls = _install_fakes(monkeypatch, "sql")
    s = orchestrator.run_orchestrator("How many projects?")
    assert s["route"] == "sql"
    assert s.get("sql_result") is not None
    assert s.get("retrieval_result") is None
    assert "synthesis" not in calls


def test_retrieval_only_route(monkeypatch):
    _install_fakes(monkeypatch, "retrieval")
    s = orchestrator.run_orchestrator("What is onboarding?")
    assert s["route"] == "retrieval"
    assert s.get("retrieval_result") is not None
    assert s.get("sql_result") is None


def test_both_route_runs_both_tools_then_synthesizes(monkeypatch):
    calls = _install_fakes(monkeypatch, "both")
    s = orchestrator.run_orchestrator("Count consultants and explain onboarding")
    assert s["route"] == "both"
    assert s["sql_result"] is not None and s["retrieval_result"] is not None
    assert "synthesis" in calls
    assert "[SQL Agent]" in s["final_answer"] and "[Retrieval Agent" in s["final_answer"]


def test_unanswerable_route_declines_without_tools(monkeypatch):
    _install_fakes(monkeypatch, "none")
    s = orchestrator.run_orchestrator("What will our stock price be?")
    assert s.get("sql_result") is None and s.get("retrieval_result") is None
    assert "can't answer" in s["final_answer"]


def test_unknown_router_reply_defaults_to_both(monkeypatch):
    _install_fakes(monkeypatch, "banana")
    s = orchestrator.run_orchestrator("Something odd")
    assert s["route"] == "both"


def test_history_is_capped(monkeypatch):
    _install_fakes(monkeypatch, "sql")
    long_history = [{"question": f"q{i}", "answer": f"a{i}"} for i in range(10)]
    s = orchestrator.run_orchestrator("Follow-up", long_history)
    assert len(s["history"]) == MAX_HISTORY_TURNS
    assert s["history"][-1]["question"] == "Follow-up"