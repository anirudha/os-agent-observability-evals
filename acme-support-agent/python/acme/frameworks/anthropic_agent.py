"""Anthropic adapter — tool-calling loop with the Messages API.

Install: pip install "opensearch-genai-observability-sdk-py[anthropic]"
"""

from __future__ import annotations

import os

from ..observability import enrich
from ..tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, SYSTEM_PROMPT

MODEL = os.environ.get("ACME_MODEL", "claude-opus-4-8")


def _anthropic_tools():
    return [
        {"name": s["name"], "description": s["description"], "input_schema": s["parameters"]}
        for s in TOOL_SCHEMAS
    ]


def run_turn(question: str, history: list[dict]) -> str:
    import anthropic

    client = anthropic.Anthropic()
    enrich(model=MODEL, provider="anthropic")

    messages = [*history, {"role": "user", "content": question}]

    for _ in range(5):
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT,
            tools=_anthropic_tools(), messages=messages,
        )
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")

        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "tool_use":
                fn = TOOL_FUNCTIONS[block.name]
                result = fn(**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
        messages.append({"role": "user", "content": tool_results})

    return "Sorry, I couldn't complete that request."
