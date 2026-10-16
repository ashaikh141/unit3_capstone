import os
import re

import psycopg2
from dotenv import load_dotenv

from bedrock_client import invoke_claude
from schema_context import SCHEMA_CONTEXT
from sql_validator import validate_sql

load_dotenv()

MAX_HISTORY_TURNS = 3
CANNOT_ANSWER = "CANNOT_ANSWER"
TOKEN_LOG = []


def call_claude(step, prompt, max_tokens=500):
    result = invoke_claude(prompt, max_tokens=max_tokens)
    TOKEN_LOG.append({
        "step": step,
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    })
    return result["text"]


def format_history(history):
    if not history:
        return ""
    lines = ["Previous conversation (use it to understand words like 'they', 'their', 'that project'):"]
    for turn in history[-MAX_HISTORY_TURNS:]:
        lines.append(f"Question: {turn['question']}")
        if turn.get("sql"):
            lines.append(f"SQL used: {turn['sql']}")
        lines.append(f"Answer: {turn['answer']}")
    return "\n".join(lines) + "\n\n"


def clean_sql(text):
    text = text.strip()
    fenced = re.search(r"```(?:sql)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    return text


def generate_sql(question, history=None):
    prompt = f"""You are an expert PostgreSQL analyst. Write one SQL query that answers the question.

Database schema:
{SCHEMA_CONTEXT}
{format_history(history)}Rules:
- Return ONLY the SQL query. No explanation, no markdown, no code fences.
- Write a single SELECT statement.
- Use only the tables and columns listed in the schema.
- Use the exact allowed values listed in the schema (e.g. status = 'active').
- If the question cannot be answered from this schema, return exactly: {CANNOT_ANSWER}

Question: {question}
SQL:"""
    return clean_sql(call_claude("sql_generation", prompt))


def get_connection():
    return psycopg2.connect(
        host=os.getenv("RDS_HOST"),
        port=os.getenv("RDS_PORT", "5432"),
        dbname=os.getenv("RDS_DATABASE"),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        connect_timeout=10,
    )


def execute_query(sql):
    validation = validate_sql(sql)
    if not validation["valid"]:
        return {"success": False, "columns": [], "rows": [], "row_count": 0,
                "error": f"Blocked by validator: {validation['reason']}",
                "validation": "BLOCKED", "validation_reason": validation["reason"]}

    result = _run_validated_query(sql)
    result["validation"] = "PASSED"
    result["validation_reason"] = validation["reason"]
    return result


def _run_validated_query(sql):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        if cur.description:
            columns = [d[0] for d in cur.description]
            rows = [list(r) for r in cur.fetchall()]
        else:
            columns, rows = [], []
        return {"success": True, "columns": columns, "rows": rows, "row_count": len(rows), "error": None}
    except Exception as e:
        return {"success": False, "columns": [], "rows": [], "row_count": 0, "error": str(e).strip()}
    finally:
        if conn:
            conn.rollback()
            conn.close()


def interpret_results(question, sql, result, history=None):
    rows_text = "\n".join(" | ".join(str(v) for v in r) for r in result["rows"][:50])
    prompt = f"""{format_history(history)}A user asked: {question}

This SQL was run:
{sql}

Columns: {result['columns']}
Rows ({result['row_count']} total, first 50 shown):
{rows_text or '(no rows)'}

Answer the user's question in one to three plain-English sentences, using only these results.
If there are no rows, say that no matching data was found. Do not mention SQL."""
    return call_claude("result_interpretation", prompt).strip()


def sql_agent(question, history=None):
    log_start = len(TOKEN_LOG)
    response = {"question": question, "sql": None, "success": False,
                "answer": None, "columns": [], "rows": [], "error": None,
                "validation": "NOT_RUN", "validation_reason": None}

    try:
        sql = generate_sql(question, history)
    except Exception as e:
        response["error"] = str(e)
        response["answer"] = "Sorry, I couldn't reach the language model to answer that."
        return finish(response, log_start)

    response["sql"] = sql
    if sql.strip().upper() == CANNOT_ANSWER:
        response["answer"] = ("I can't answer that from this database. It only has clients, "
                              "projects, consultants, and invoices.")
        return finish(response, log_start)

    result = execute_query(sql)
    response.update(columns=result["columns"], rows=result["rows"], error=result["error"],
                    validation=result["validation"], validation_reason=result["validation_reason"])
    if result["validation"] == "BLOCKED":
        response["answer"] = ("I won't run that. This assistant can only read data, and the query "
                              f"was blocked by the safety check ({result['validation_reason']}).")
        return finish(response, log_start)
    if not result["success"]:
        response["answer"] = f"Sorry, the query I wrote didn't run. Database error: {result['error']}"
        return finish(response, log_start)

    response["success"] = True
    response["answer"] = interpret_results(question, sql, result, history)
    return finish(response, log_start)


def finish(response, log_start):
    calls = TOKEN_LOG[log_start:]
    response["token_usage"] = {
        "calls": calls,
        "input_tokens": sum(c["input_tokens"] for c in calls),
        "output_tokens": sum(c["output_tokens"] for c in calls),
    }
    return response


def print_result(r):
    print("=" * 80)
    print("Q:  ", r["question"])
    print("SQL:", r["sql"])
    reason = f" ({r['validation_reason']})" if r["validation"] == "BLOCKED" else ""
    print(f"Validation: {r['validation']}{reason}")
    print("A:  ", r["answer"])
    print(f"Tokens: {r['token_usage']['input_tokens']} in / {r['token_usage']['output_tokens']} out")
    print()

# Shared Tool Registry: standard interface

def run_sql_agent(question: str, history=None) -> dict:
    result = sql_agent(question, history)
    sql = result["sql"]
    has_sql = bool(sql) and sql.strip().upper() != CANNOT_ANSWER
    return {
        "success": result["success"],
        "answer": result["answer"],
        "sources": [f"SQL: {sql}"] if has_sql else [],
        "metadata": {
            "sql": sql,
            "validation": result["validation"],
            "validation_reason": result["validation_reason"],
            "row_count": len(result["rows"]),
            "error": result["error"],
            "token_usage": result["token_usage"],
        },
    }