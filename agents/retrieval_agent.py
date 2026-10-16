import os
import re

import boto3
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from onnx_embed import get_embedding

from bedrock_client import invoke_claude

load_dotenv()

REGION = "us-east-1"
INDEX_NAME = "documents"
NOT_FOUND = "I cannot find this information in the available documents."


# Part 1: the retrieval function



_client = None


def get_opensearch_client():
    global _client
    if _client is None:
        endpoint = os.getenv("OPENSEARCH_ENDPOINT").replace("https://", "").rstrip("/")
        credentials = boto3.Session().get_credentials()
        auth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, "es",
                        session_token=credentials.token)
        _client = OpenSearch(
            hosts=[{"host": endpoint, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=60,
        )
    return _client


def retrieve(question: str, top_k: int = 5, expand_top: int = 2) -> list[dict]:
    query_vector = get_embedding(question)
    client = get_opensearch_client()
    response = client.search(
        index=INDEX_NAME,
        body={
            "size": top_k,
            "_source": ["content", "source", "chunk_number"],
            "query": {"knn": {"embedding": {"vector": query_vector, "k": top_k}}},
        },
    )
    chunks = [
        {
            "content": hit["_source"]["content"],
            "source": hit["_source"]["source"],
            "chunk_number": hit["_source"]["chunk_number"],
            "score": hit["_score"],
        }
        for hit in response["hits"]["hits"]
    ]
    return add_neighbor_chunks(chunks, client, expand_top)


def add_neighbor_chunks(chunks: list[dict], client, expand_top: int) -> list[dict]:
    """For the best few hits, also fetch the chunk just before and just after it in the same
    document, so an answer split across a chunk boundary isn't cut in half."""
    have = {(c["source"], c["chunk_number"]) for c in chunks}
    wanted = []
    for c in chunks[:expand_top]:
        for n in (c["chunk_number"] - 1, c["chunk_number"] + 1):
            if n >= 0 and (c["source"], n) not in have:
                have.add((c["source"], n))
                wanted.append((c, n))
    if not wanted:
        return chunks

    ids = [f"{c['source']}-{n}" for c, n in wanted]
    docs = client.mget(index=INDEX_NAME, body={"ids": ids})["docs"]
    neighbors = [
        {
            "content": doc["_source"]["content"],
            "source": doc["_source"]["source"],
            "chunk_number": doc["_source"]["chunk_number"],
            "score": parent["score"],
            "neighbor_of": f"{parent['source']} chunk {parent['chunk_number']}",
        }
        for (parent, _), doc in zip(wanted, docs)
        if doc.get("found")
    ]
    return chunks + neighbors

# Part 2: retrieval wrapped as a tool

tools = [
    {
        "name": "search_documents",
        "description": (
            "Search the firm's indexed policy documents (onboarding, invoicing and payment, project delivery, "
            "consultant grades and utilization targets, expenses and travel, remote work and data security) "
            "for passages relevant to a question. Use it for questions about processes, rules, and policies. "
            "Do NOT use it for numbers about specific clients, projects, consultants, or invoices; those are "
            "in the SQL database."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The question or search phrase"},
            },
            "required": ["query"],
        },
    }
]


def search_documents_tool(query: str) -> str:
    chunks = retrieve(query)
    if not chunks:
        return "No relevant documents found."
    return "\n\n".join(f"[Source: {c['source']}]\n{c['content']}" for c in chunks)


# Part 3: generating a cited answer

def generate_cited_answer(question: str, chunks: list[dict]) -> dict:
    context = "\n\n".join(f"[Source: {c['source']}]\n{c['content']}" for c in chunks)
    prompt = f"""Answer the question using ONLY the context provided below.
If the answer is not in the context, reply with exactly: "{NOT_FOUND}"
Always cite the source document(s) you used, in the format [Source: filename.pdf].

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    result = invoke_claude(prompt, max_tokens=500)
    return {
        "text": result["text"].strip(),
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
    }


# Part 4: assembling the retrieval agent

def retrieval_agent(question: str) -> dict:
    chunks = retrieve(question)
    if not chunks:
        return {"answer": "No relevant documents found.", "sources": [], "chunks": [],
                "grounded": False, "token_usage": {"input_tokens": 0, "output_tokens": 0}}

    generated = generate_cited_answer(question, chunks)
    answer = generated["text"]
    return {
        "answer": answer,
        "sources": sorted({c["source"] for c in chunks}),
        "chunks": chunks,
        "grounded": check_grounding(answer, chunks),
        "token_usage": {"input_tokens": generated["input_tokens"],
                        "output_tokens": generated["output_tokens"]},
    }


# Part 5: a simple automated grounding check

def check_grounding(answer: str, chunks: list[dict]) -> bool:
    """Quick heuristic: every source the answer cites must be one the retrieval actually returned.
    An answer with no citations only counts as grounded if it is the 'cannot find' fallback."""
    retrieved = {os.path.basename(c["source"]) for c in chunks}
    cited = {os.path.basename(s.strip()) for s in re.findall(r"\[Source:\s*([^\]]+)\]", answer)}
    if not cited:
        return "cannot find" in answer.lower()
    return cited.issubset(retrieved)

# Shared Tool Registry: standard interface

def run_retrieval_agent(question: str) -> dict:
    result = retrieval_agent(question)
    chunks = result["chunks"]
    usage = result["token_usage"]
    return {
        "success": len(chunks) > 0,
        "answer": result["answer"],
        "sources": list(dict.fromkeys(c["source"] for c in chunks)),
        "metadata": {
            "chunk_count": len(chunks),
            "chunk_scores": [
                {"source": c["source"], "chunk_number": c.get("chunk_number"),
                 "score": round(c["score"], 3), "neighbor": bool(c.get("neighbor_of"))}
                for c in chunks
            ],
            "grounded": result["grounded"],
            "answer_found": "cannot find" not in result["answer"].lower(),
            "token_usage": {
                "calls": [{"step": "retrieval_answer_generation",
                           "input_tokens": usage["input_tokens"],
                           "output_tokens": usage["output_tokens"]}],
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
            },
        },
    }