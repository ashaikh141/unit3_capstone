"""
bedrock_client.py — shared helper for calling Claude via Bedrock.

Introduced in this lab (Build a SQL Query Agent) since it's the first lab in
the sequence needing Claude. Every subsequent lab this week that calls Claude
(Retrieval Agent, Shared Tool Registry, the Orchestrator, the Capstone) reuses
this exact module rather than each reimplementing its own Bedrock call.

This calls Claude via Bedrock, not the direct Anthropic SDK — students in
this environment don't have direct Anthropic API keys, so the
inference-profile ARN pattern below is the only path to Claude Sonnet 4.6
available here.
"""
import boto3
import json

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")


def get_model_id() -> str:
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    return f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.anthropic.claude-sonnet-4-6"


def invoke_claude(prompt: str, max_tokens: int = 500) -> dict:
    """
    Sends a single-turn prompt to Claude via Bedrock and returns the response
    text alongside token usage, so every caller can log tokenomics data
    consistently without needing to know Bedrock's specific response shape.
    """
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = bedrock.invoke_model(modelId=get_model_id(), body=json.dumps(body))
    result = json.loads(response["body"].read())
    return {
        "text": result["content"][0]["text"],
        "input_tokens": result["usage"]["input_tokens"],
        "output_tokens": result["usage"]["output_tokens"]
    }