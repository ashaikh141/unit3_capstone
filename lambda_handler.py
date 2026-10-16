"""
lambda_handler.py -- wraps the orchestrator in the format Lambda expects.
"""
import json

from tokenomics_logger import logged_orchestrator, run_traced_query

orchestrator = logged_orchestrator


def _read_question(event):
    body = event.get("body", event)
    if isinstance(body, str):
        body = json.loads(body or "{}")
    return (body.get("question") or "").strip()


def handler(event, context):
    try:
        question = _read_question(event)
        if not question:
            return {"statusCode": 400, "body": json.dumps({"error": "question is required"})}

        result = run_traced_query(orchestrator, question)

        sql_validation = None
        if result.get("sql_result"):
            sql_validation = result["sql_result"].get("metadata", {}).get("validation")

        sources = {}
        if result.get("sql_result"):
            sources["sql_agent"] = result["sql_result"]["sources"]
        if result.get("retrieval_result"):
            sources["retrieval_agent"] = result["retrieval_result"]["sources"]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "answer": result["final_answer"],
                "route": result["route"],
                "sql_validation": sql_validation,
                "sources": sources,
                "token_usage": result.get("token_usage", {}),
                "token_usage_by_component": result.get("token_usage_by_component", {}),
                "cost_breakdown": result.get("cost_breakdown", {}),
                "trace_id": result.get("trace_id"),
            }, default=str),
        }
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}