import json

from orchestrator import run_orchestrator


def lambda_handler(event, context):
    body = event or {}
    if isinstance(body.get("body"), str):
        body = json.loads(body["body"])

    question = str(body.get("question", "")).strip()
    history = body.get("history") or []
    if not question:
        return {"error": 'Send a JSON payload like {"question": "...", "history": []}'}

    state = run_orchestrator(question, history)
    sql_result = state.get("sql_result")
    sql_validation = (sql_result or {}).get("metadata", {}).get("sql_validation", "NOT_RUN")

    response = {
        "question": question,
        "route": state.get("route"),
        "sql_validation": sql_validation,
        "answer": state.get("final_answer"),
        "sql_result": sql_result,
        "retrieval_result": state.get("retrieval_result"),
        "token_usage": {
            "total": state["token_usage"]["total"],
            "by_component": state["token_usage"]["by_component"],
        },
        "history": state.get("history"),
    }
    print(json.dumps({"event": "orchestrator_complete", "route": response["route"],
                      "sql_validation": sql_validation,
                      "token_usage_total": response["token_usage"]["total"]}))
    return json.loads(json.dumps(response, default=str))


handler = lambda_handler