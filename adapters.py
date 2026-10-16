import os

from validator import validate_sql

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DB_SCHEMA = os.getenv("DB_SCHEMA", "public")
_schema_cache = None


def get_db_connection():
    import psycopg2
    conn = psycopg2.connect(
        host=os.environ["RDS_HOST"],
        port=int(os.getenv("RDS_PORT", "5432")),
        dbname=os.environ["RDS_DATABASE"],
        user=os.environ["RDS_USER"],
        password=os.environ["RDS_PASSWORD"],
        connect_timeout=10,
    )
    conn.set_session(readonly=True, autocommit=True)
    return conn


def run_select(sql, max_rows=200):
    verdict = validate_sql(sql)
    if not verdict["valid"]:
        raise PermissionError(f"Refusing to execute SQL: {verdict['reason']}")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(max_rows)
        return [dict(zip(cols, r)) for r in rows]
    finally:
        conn.close()


def get_schema_text():
    global _schema_cache
    if _schema_cache:
        return _schema_cache
    rows = run_select(
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        f"WHERE table_schema = '{DB_SCHEMA}' ORDER BY table_name, ordinal_position",
        max_rows=2000,
    )
    tables = {}
    for r in rows:
        tables.setdefault(r["table_name"], []).append(f"{r['column_name']} ({r['data_type']})")
    _schema_cache = "\n".join(f"TABLE {t}: {', '.join(cols)}" for t, cols in tables.items())
    return _schema_cache


INDEX = os.getenv("OPENSEARCH_INDEX", "documents")
VECTOR_FIELD = os.getenv("VECTOR_FIELD", "embedding")
TEXT_FIELD = os.getenv("TEXT_FIELD", "text")
SOURCE_FIELD = os.getenv("SOURCE_FIELD", "source")
_os_client = None


def get_opensearch_client():
    global _os_client
    if _os_client is None:
        from agents.retrieval_agent import get_opensearch_client as lab_client
        _os_client = lab_client()
    return _os_client


def count_documents():
    res = get_opensearch_client().search(
        index=INDEX,
        body={"size": 0, "track_total_hits": True, "query": {"match_all": {}}},
    )
    return res["hits"]["total"]["value"]


def get_index_fields():
    mapping = get_opensearch_client().indices.get_mapping(index=INDEX)
    props = next(iter(mapping.values()))["mappings"].get("properties", {})
    return {name: spec.get("type", "object") for name, spec in props.items()}


def embed_query(text):
    from onnx_embed import get_embedding
    return [float(x) for x in get_embedding(text)]


def retrieve_chunks(question, k=4):
    body = {
        "size": k,
        "query": {"knn": {VECTOR_FIELD: {"vector": embed_query(question), "k": k}}},
        "_source": {"excludes": [VECTOR_FIELD]},
    }
    hits = get_opensearch_client().search(index=INDEX, body=body)["hits"]["hits"]
    return [
        {
            "doc": str(h["_source"].get(SOURCE_FIELD, h["_id"])),
            "text": str(h["_source"].get(TEXT_FIELD, "")),
            "score": round(float(h["_score"]), 4),
        }
        for h in hits
    ]