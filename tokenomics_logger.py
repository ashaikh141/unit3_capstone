import json
import os
import uuid
from datetime import datetime, timezone

from langgraph.graph import END, StateGraph

from orchestrator import (
    OrchestratorState,
    call_retrieval_agent,
    call_sql_agent,
    route_question,
    synthesize,
)

# Lambda's code directory is read-only; only /tmp is writable there.
LOG_PATH = "/tmp/agent_decisions.jsonl" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "agent_decisions.jsonl"

# USD per 1,000 tokens. Check these against Amazon Bedrock pricing for the model in bedrock_client.py.
COST_PER_1K_INPUT = 0.003
COST_PER_1K_OUTPUT = 0.015

_current_trace = {"id": None}


# Part 1: Logging agent decisions

def log_decision(stage: str, question: str, details: dict):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": _current_trace["id"],
        "stage": stage,
        "question": question,
        "details": details,
    }
    print(f"[LOG] {stage}: {json.dumps(details, default=str)}")
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")


def _input_tokens(tokens):
    tokens = tokens or {}
    return tokens.get("input_tokens", tokens.get("input", 0))


def _output_tokens(tokens):
    tokens = tokens or {}
    return tokens.get("output_tokens", tokens.get("output", 0))


def cost(tokens) -> float:
    return (_input_tokens(tokens) / 1000) * COST_PER_1K_INPUT + \
           (_output_tokens(tokens) / 1000) * COST_PER_1K_OUTPUT


def _claude_calls(token_usage):
    calls = (token_usage or {}).get("calls", [])
    return [{**c, "usd": round(cost(c), 6)} for c in calls]


def route_question_logged(state):
    result = route_question(state)
    log_decision("routing", state["question"], {"route": result["route"], "classifier": "keywords (no Claude call)"})
    return result


def call_sql_agent_logged(state):
    result = call_sql_agent(state)
    r = result.get("sql_result")
    if r is None:
        log_decision("sql_agent", state["question"], {"ran": False, "reason": f"route={state['route']}"})
    else:
        meta = r["metadata"]
        log_decision("sql_agent", state["question"], {
            "ran": True,
            "success": r["success"],
            "validation": meta.get("validation"),
            "validation_reason": meta.get("validation_reason"),
            "sql": meta.get("sql"),
            "row_count": meta.get("row_count"),
            "claude_calls": _claude_calls(meta.get("token_usage")),
        })
    return result


def call_retrieval_agent_logged(state):
    result = call_retrieval_agent(state)
    r = result.get("retrieval_result")
    if r is None:
        log_decision("retrieval_agent", state["question"], {"ran": False, "reason": f"route={state['route']}"})
    else:
        meta = r["metadata"]
        log_decision("retrieval_agent", state["question"], {
            "ran": True,
            "success": r["success"],
            "chunk_count": meta.get("chunk_count"),
            "grounded": meta.get("grounded"),
            "answer_found": meta.get("answer_found"),
            "sources": r["sources"],
            "claude_calls": _claude_calls(meta.get("token_usage")),
        })
    return result


def synthesize_logged(state):
    result = synthesize(state)
    usage = result.get("token_usage") or {}
    log_decision("synthesizer", state["question"], {
        "used_sql_result": bool(state.get("sql_result") and state["sql_result"].get("success")),
        "used_retrieval_result": bool(state.get("retrieval_result") and state["retrieval_result"].get("success")),
        "claude_calls": [{"step": "synthesis", "input_tokens": _input_tokens(usage),
                          "output_tokens": _output_tokens(usage), "usd": round(cost(usage), 6)}],
    })
    return result


def build_logged_orchestrator():
    graph = StateGraph(OrchestratorState)
    graph.add_node("router", route_question_logged)
    graph.add_node("sql_agent", call_sql_agent_logged)
    graph.add_node("retrieval_agent", call_retrieval_agent_logged)
    graph.add_node("synthesizer", synthesize_logged)
    graph.set_entry_point("router")
    graph.add_edge("router", "sql_agent")
    graph.add_edge("sql_agent", "retrieval_agent")
    graph.add_edge("retrieval_agent", "synthesizer")
    graph.add_edge("synthesizer", END)
    return graph.compile()


logged_orchestrator = build_logged_orchestrator()


# Part 3: Cost per token at multi-agent scale

def calculate_full_query_cost(sql_tokens: dict, retrieval_tokens: dict, synthesis_tokens: dict) -> dict:
    sql_cost = cost(sql_tokens) if sql_tokens else 0
    retrieval_cost = cost(retrieval_tokens) if retrieval_tokens else 0
    synthesis_cost = cost(synthesis_tokens) if synthesis_tokens else 0
    total = sql_cost + retrieval_cost + synthesis_cost
    return {
        "sql_agent_cost": round(sql_cost, 6),
        "retrieval_agent_cost": round(retrieval_cost, 6),
        "synthesis_cost": round(synthesis_cost, 6),
        "total_cost": round(total, 6),
        "cost_per_1k_queries": round(total * 1000, 2),
    }


def component_tokens(result: dict) -> dict:
    sql_usage = (result.get("sql_result") or {}).get("metadata", {}).get("token_usage")
    retrieval_usage = (result.get("retrieval_result") or {}).get("metadata", {}).get("token_usage")
    synthesis_usage = result.get("token_usage")
    return {
        "sql_agent": {"input": _input_tokens(sql_usage), "output": _output_tokens(sql_usage)},
        "retrieval_agent": {"input": _input_tokens(retrieval_usage), "output": _output_tokens(retrieval_usage)},
        "synthesis": {"input": _input_tokens(synthesis_usage), "output": _output_tokens(synthesis_usage)},
    }


# Part 2: Tracing query chains

def run_traced_query(orchestrator, question: str) -> dict:
    trace_id = str(uuid.uuid4())[:8]
    _current_trace["id"] = trace_id
    log_decision("query_start", question, {"trace_id": trace_id})

    result = orchestrator.invoke({
        "question": question, "route": None, "sql_result": None,
        "retrieval_result": None, "final_answer": None, "token_usage": None,
    })

    sql_meta = (result.get("sql_result") or {}).get("metadata", {})
    retrieval_meta = (result.get("retrieval_result") or {}).get("metadata", {})
    breakdown = calculate_full_query_cost(
        sql_meta.get("token_usage"), retrieval_meta.get("token_usage"), result.get("token_usage")
    )
    tokens = component_tokens(result)

    log_decision("query_complete", question, {
        "trace_id": trace_id,
        "route": result["route"],
        "sql_validation": sql_meta.get("validation"),
        "retrieval_chunk_count": retrieval_meta.get("chunk_count"),
        "token_usage_by_component": tokens,
        "cost_breakdown": breakdown,
    })

    result["trace_id"] = trace_id
    result["token_usage_by_component"] = tokens
    result["cost_breakdown"] = breakdown
    _current_trace["id"] = None
    return result