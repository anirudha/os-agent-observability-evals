"""Acme Support Agent on Amazon Bedrock AgentCore Runtime — one clean flow.

AgentCore Runtime hosts the agent behind a managed HTTP endpoint. The contract is
a single @app.entrypoint function that takes the request payload and returns the
response. Everything else — the agent loop, the tools, the observability — is the
same shared core used by every other variant.

We instrument inside the entrypoint so each invocation is one invoke_agent trace,
exported to the OpenSearch stack via OTLP. In AgentCore, point
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT at your collector (in-VPC for production).

Local dev:    python agent.py            # runs the AgentCore dev server on :8080
Deploy:       see README.md (agentcore configure && agentcore launch)

Docs: https://aws.amazon.com/bedrock/agentcore/
"""

from __future__ import annotations

from bedrock_agentcore import BedrockAgentCoreApp

from acme_shared import setup_observability, observe, enrich, Op
from acme_shared.tools import lookup_order, check_inventory, search_policy, SYSTEM_PROMPT

# Configure observability once at import/cold-start.
setup_observability(service_name="acme-support-agent")

app = BedrockAgentCoreApp()

# Default model is a Bedrock-hosted Claude; AgentCore runs with the task role's
# AWS credentials, so no keys are needed in the container.
MODEL = "anthropic.claude-3-5-sonnet-20240620-v1:0"


def _bedrock_tool_config():
    from acme_shared.tools import TOOL_SCHEMAS
    return {"tools": [
        {"toolSpec": {"name": s["name"], "description": s["description"],
                      "inputSchema": {"json": s["parameters"]}}}
        for s in TOOL_SCHEMAS
    ]}


_TOOLS = {"lookup_order": lookup_order, "check_inventory": check_inventory,
          "search_policy": search_policy}


@observe(op=Op.INVOKE_AGENT, name="acme-support-agent")
def _run_agent(question: str, conversation_id: str) -> str:
    import boto3

    enrich(provider="aws.bedrock", model=MODEL,
           session_id=conversation_id)  # session_id -> gen_ai.conversation.id
    client = boto3.client("bedrock-runtime")
    messages = [{"role": "user", "content": [{"text": question}]}]

    for _ in range(5):
        resp = client.converse(
            modelId=MODEL, messages=messages,
            system=[{"text": SYSTEM_PROMPT}], toolConfig=_bedrock_tool_config(),
        )
        out = resp["output"]["message"]
        messages.append(out)
        if resp.get("stopReason") != "tool_use":
            return "".join(b["text"] for b in out["content"] if "text" in b)
        results = []
        for block in out["content"]:
            if "toolUse" in block:
                tu = block["toolUse"]
                r = _TOOLS[tu["name"]](**tu["input"])
                results.append({"toolResult": {"toolUseId": tu["toolUseId"],
                                                "content": [{"json": r}]}})
        messages.append({"role": "user", "content": results})
    return "Sorry, I couldn't complete that request."


@app.entrypoint
def invoke(payload: dict) -> dict:
    """AgentCore Runtime entrypoint.

    payload: {"prompt": "...", "conversation_id": "..."} (conversation_id optional)
    returns: {"response": "..."}
    """
    question = payload.get("prompt", "")
    conversation_id = payload.get("conversation_id", "agentcore-session")
    answer = _run_agent(question, conversation_id)
    return {"response": answer}


if __name__ == "__main__":
    # Local AgentCore dev server (mirrors the deployed runtime contract).
    app.run()
