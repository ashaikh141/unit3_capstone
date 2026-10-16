import json
import os
import re
import time

import adapters
import llm
from conversation import history_block
from validator import validate_sql

SQL_DIALECT = os.getenv("SQL_DIALECT", "PostgreSQL")
TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "4"))
MAX_CHUNK_CHARS = 1500

SQL_SYSTEM = """You translate a user's request into exactly ONE {dialect} SQL statement for this database:

{schema}

Rules:
- Output ONLY the SQL. No explanation, no markdown, no code fences.
- Use only the tables and columns listed above.
- Translate the request faithfully. A separate validator decides whether the statement is allowed to run.
- If earlier conversation is provided, use it to resolve words like "their", "that project", "those clients".
- If only PART of the request can be answered from these tables, write SQL for that part and ignore the rest.
- Only if NO part of the request can be answered from these tables, output exactly: CANNOT_ANSWER"""

INTERPRET_SYSTEM = """You explain SQL query results to a business user in 1-3 sentences.
Use only the rows provided. If there are no rows, say no matching records were found.
Never invent numbers."""

RETRIEVAL_SYSTEM = """You answer questions using ONLY the document excerpts provided.
Each excerpt starts with its document name in square brackets.
- Put the document name in square brackets after each fact, e.g. [onboarding_guide.md].
- Answer only the parts of the question the excerpts cover. Do not mention parts that need database records such as counts, totals, or specific clients; another agent handles those.
- If the excerpts cover no part of the question, reply exactly: NOT_FOUND"""


def _result(success, answer, sources, metadata, start):
    metadata["latency_s"] = round(time.time() - start, 2)
    return {
        "success": bool(success),
        "answer": str(answer),
        "sources": list(sources),
        "metadata": metadata,
    }


def _clean_sql(text):
    text = text.strip()
    text = re.sub(r"^```(?:sql)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def run_sql_agent(question, history=None):
    start = time.time()
    meta = {"tool": "sql_agent", "sql_validation": "NOT_RUN"}
    sql = ""
    try:
        system = SQL_SYSTEM.format(dialect=SQL_DIALECT, schema=adapters.get_schema_text())
        raw = llm.call_claude("sql_generation", system,
                              history_block(history) + f"Request: {question}", max_tokens=400)
        sql = _clean_sql(raw)
        meta["sql"] = sql

        if sql.upper().startswith("CANNOT_ANSWER"):
            meta["sql_validation"] = "NOT_APPLICABLE"
            return _result(False, "The database does not contain the information needed to answer this.",
                           [], meta, start)

        verdict = validate_sql(sql)
        meta["sql_validation"] = verdict["status"]
        meta["validation_reason"] = verdict["reason"]
        if not verdict["valid"]:
            return _result(False,
                           f"Blocked: the generated query failed validation ({verdict['reason']}). "
                           "Nothing was executed.",
                           [sql], meta, start)

        rows = adapters.run_select(sql)
        meta["row_count"] = len(rows)
        preview = json.dumps(rows[:50], default=str)
        answer = llm.call_claude(
            "sql_interpretation", INTERPRET_SYSTEM,
            f"Question: {question}\nSQL: {sql}\nRows returned: {len(rows)} (up to 50 shown)\n{preview}",
            max_tokens=400)
        return _result(True, answer.strip(), [sql], meta, start)
    except Exception as exc:
        meta["error"] = f"{type(exc).__name__}: {exc}"
        return _result(False, f"The SQL agent hit an error: {meta['error']}",
                       [sql] if sql else [], meta, start)


def run_retrieval_agent(question, history=None):
    start = time.time()
    meta = {"tool": "retrieval_agent"}
    try:
        search_text = question
        if history:
            search_text = f"{history[-1].get('question', '')} {question}"
        chunks = adapters.retrieve_chunks(search_text, k=TOP_K)
        meta["chunk_scores"] = [{"doc": c["doc"], "score": c["score"]} for c in chunks]

        if not chunks:
            meta["grounded"] = False
            return _result(False, "No relevant documents were found.", [], meta, start)

        context = "\n\n".join(f"[{c['doc']}]\n{c['text'][:MAX_CHUNK_CHARS]}" for c in chunks)
        answer = llm.call_claude(
            "retrieval_answer", RETRIEVAL_SYSTEM,
            history_block(history) + f"Excerpts:\n{context}\n\nQuestion: {question}",
            max_tokens=500).strip()
        retrieved_docs = sorted({c["doc"] for c in chunks})

        if answer.upper().startswith("NOT_FOUND"):
            meta["grounded"] = False
            return _result(False, "The company documents don't cover this.", retrieved_docs, meta, start)

        cited = [d for d in retrieved_docs if d in answer]
        meta["grounded"] = bool(cited)
        meta["cited_docs"] = cited
        return _result(True, answer, cited or retrieved_docs, meta, start)
    except Exception as exc:
        meta["error"] = f"{type(exc).__name__}: {exc}"
        return _result(False, f"The retrieval agent hit an error: {meta['error']}", [], meta, start)