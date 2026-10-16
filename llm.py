import json
import os
import time
from datetime import datetime, timezone

import boto3
from botocore.config import Config

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from bedrock_client import get_model_id
    _DEFAULT_MODEL = get_model_id()
except Exception:
    _DEFAULT_MODEL = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

MODEL_ID = os.getenv("BEDROCK_MODEL_ID") or _DEFAULT_MODEL
REGION = os.getenv("AWS_REGION") or boto3.Session().region_name or "us-east-1"

PRICE_IN_PER_M = float(os.getenv("PRICE_IN_PER_M", "3.30"))
PRICE_OUT_PER_M = float(os.getenv("PRICE_OUT_PER_M", "16.50"))

ON_LAMBDA = bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
LOG_PATH = "/tmp/tokenomics.jsonl" if ON_LAMBDA else os.path.join("logs", "tokenomics.jsonl")

_client = boto3.client(
    "bedrock-runtime",
    region_name=REGION,
    config=Config(retries={"max_attempts": 6, "mode": "adaptive"}),
)
_calls = []


def reset_usage():
    _calls.clear()


def call_claude(component, system, user, max_tokens=800, temperature=0.0):
    start = time.time()
    response = _client.converse(
        modelId=MODEL_ID,
        system=[{"text": system}],
        messages=[{"role": "user", "content": [{"text": user}]}],
        inferenceConfig={"maxTokens": max_tokens, "temperature": temperature},
    )
    text = "".join(b.get("text", "") for b in response["output"]["message"]["content"])

    usage = response.get("usage", {})
    in_tok = usage.get("inputTokens", 0)
    out_tok = usage.get("outputTokens", 0)
    cost = in_tok / 1_000_000 * PRICE_IN_PER_M + out_tok / 1_000_000 * PRICE_OUT_PER_M

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "model": MODEL_ID,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "cost_usd": round(cost, 6),
        "latency_s": round(time.time() - start, 2),
    }
    _calls.append(entry)
    print(f"[TOKENS] {component:<20} in={in_tok:>6}  out={out_tok:>5}  "
          f"cost=${cost:.6f}  ({entry['latency_s']}s)", flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass
    return text


def get_usage():
    by_component = {}
    for c in _calls:
        b = by_component.setdefault(
            c["component"], {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        b["calls"] += 1
        b["input_tokens"] += c["input_tokens"]
        b["output_tokens"] += c["output_tokens"]
        b["cost_usd"] = round(b["cost_usd"] + c["cost_usd"], 6)
    total = {
        "calls": len(_calls),
        "input_tokens": sum(c["input_tokens"] for c in _calls),
        "output_tokens": sum(c["output_tokens"] for c in _calls),
        "cost_usd": round(sum(c["cost_usd"] for c in _calls), 6),
    }
    return {"total": total, "by_component": by_component, "calls": list(_calls)}