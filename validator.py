
import re

BLOCKED_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "CREATE",
    "GRANT", "REVOKE", "MERGE", "EXEC", "EXECUTE", "CALL", "COPY", "INTO",
    "ATTACH", "DETACH", "PRAGMA", "VACUUM", "LOCK", "SET",
]
_BLOCKED_RE = re.compile(r"\b(" + "|".join(BLOCKED_KEYWORDS) + r")\b", re.IGNORECASE)


def _strip_strings_and_comments(sql):
    # Strings first, so '--' or '/*' inside a string can't hide anything
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql.strip()


def _blocked(reason):
    return {"valid": False, "status": "BLOCKED", "reason": reason}


def validate_sql(sql):
    if not sql or not sql.strip():
        return _blocked("Empty query")

    body = _strip_strings_and_comments(sql).rstrip(";").strip()

    
    if ";" in body:
        return _blocked("Stacked query: more than one statement is not allowed")

    
    first_word = body.split(None, 1)[0].upper() if body else ""
    if first_word not in ("SELECT", "WITH"):
        return _blocked(f"Only SELECT queries are allowed (statement starts with {first_word or 'nothing'})")

    
    match = _BLOCKED_RE.search(body)
    if match:
        return _blocked(f"Blocked keyword: {match.group(1).upper()}")

    return {"valid": True, "status": "PASSED", "reason": "Single read-only SELECT"}