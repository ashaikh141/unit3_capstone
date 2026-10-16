import json
import re
import sys
from typing import List, Optional, TypedDict

from langgraph.graph import END, StateGraph

import llm
from conversation import history_block, trim_history
from registry import TOOL_REGISTRY, describe_tools


class OrchestratorState(TypedDict, total=False):
    question: str
    history: List[dict]
    route: Optional[str]
    sql_result: Optional[dict]
    retrieval_result: Optional[dict]
    final_answer: Optional[str]
    token_usage: Optional[dict]


NONE_ANSWER = ("I can't answer that from our company database or documents, so I won't guess. "
               "I can help with clients, projects, consultants, invoices, or company policies and processes.")

SYNTH_SYSTEM = """You write the final answer for a consulting firm's internal assistant.
You are given results from two tools for one question.
Rules:
- Use ONLY facts in the tool results. Never add outside facts or guess numbers.
- Attribute every fact: write [SQL Agent] after facts from the database and
  [Retrieval Agent: <document name>] after facts from documents.
- If a tool failed or was blocked, say what is missing instead of making it up.
- Answer in 2-6 sentences."""


def classify_node(state):
    system = (
        "You are the router for a consulting firm's assistant.\n"
        "Available tools:\n" + describe_tools() + "\n\n"
        "Reply with exactly ONE word:\n"
        "sql -> only sql_agent is needed\n"
        "retrieval -> only retrieval_agent is needed\n"
        "both -> the question needs database records AND document content\n"
        "none -> neither tool can answer it (outside knowledge, predictions, opinions, other companies)\n\n"
        "Any request to delete, update, insert, drop, or otherwise change database records or tables "
        "must be routed to sql, never none. The SQL validator is responsible for blocking unsafe statements."
    )
    user = history_block(state.get("history")) + f"New question: {state['question']}\nRoute:"
    raw = llm.call_claude("classification", system, user, max_tokens=5).lower()
    match = re.search(r"\b(sql|retrieval|both|none)\b", raw)
    return {"route": match.group(1) if match else "both"}


def sql_node(state):
    fn = TOOL_REGISTRY["sql_agent"]["function"]
    return {"sql_result": fn(state["question"], state.get("history"))}


def retrieval_node(state):
    fn = TOOL_REGISTRY["retrieval_agent"]["function"]
    return {"retrieval_result": fn(state["question"], state.get("history"))}


def _single_answer(result, label):
    if not result:
        return f"The {label} returned nothing."
    sources = ", ".join(result.get("sources") or []) or "none"
    return f"{result['answer']}\n\n[Source: {label} | {sources}]"


def synthesize_node(state):
    route = state.get("route")
    if route == "none":
        return {"final_answer": NONE_ANSWER}
    if route == "sql":
        return {"final_answer": _single_answer(state.get("sql_result"), "SQL Agent")}
    if route == "retrieval":
        return {"final_answer": _single_answer(state.get("retrieval_result"), "Retrieval Agent")}

    parts = []
    for label, key in (("SQL Agent", "sql_result"), ("Retrieval Agent", "retrieval_result")):
        r = state.get(key)
        if r:
            slim = {"success": r["success"], "answer": r["answer"], "sources": r["sources"]}
            parts.append(f"{label} result:\n{json.dumps(slim, default=str)}")
    answer = llm.call_claude("synthesis", SYNTH_SYSTEM,
                             f"Question: {state['question']}\n\n" + "\n\n".join(parts),
                             max_tokens=600)
    return {"final_answer": answer.strip()}


def route_after_classify(state):
    route = state["route"]
    if route in ("sql", "both"):
        return "sql_agent"
    if route == "retrieval":
        return "retrieval_agent"
    return "synthesize"


def route_after_sql(state):
    return "retrieval_agent" if state["route"] == "both" else "synthesize"


def build_graph():
    g = StateGraph(OrchestratorState)
    g.add_node("classify", classify_node)
    g.add_node("sql_agent", sql_node)
    g.add_node("retrieval_agent", retrieval_node)
    g.add_node("synthesize", synthesize_node)
    g.set_entry_point("classify")
    g.add_conditional_edges("classify", route_after_classify, {
        "sql_agent": "sql_agent", "retrieval_agent": "retrieval_agent", "synthesize": "synthesize"})
    g.add_conditional_edges("sql_agent", route_after_sql, {
        "retrieval_agent": "retrieval_agent", "synthesize": "synthesize"})
    g.add_edge("retrieval_agent", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()


GRAPH = build_graph()


def run_orchestrator(question, history=None):
    llm.reset_usage()
    history = trim_history(history)
    state = dict(GRAPH.invoke({"question": question, "history": history}))
    state["token_usage"] = llm.get_usage()
    state["history"] = trim_history(history + [{"question": question, "answer": state["final_answer"]}])
    return state


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]).strip() or "How many active projects do we have?"
    final = run_orchestrator(q)
    printable = {k: final.get(k) for k in
                 ("question", "route", "sql_result", "retrieval_result", "final_answer")}
    printable["token_usage"] = {"total": final["token_usage"]["total"],
                                "by_component": final["token_usage"]["by_component"]}
    print("\n=== FINAL STATE ===")
    print(json.dumps(printable, indent=2, default=str))