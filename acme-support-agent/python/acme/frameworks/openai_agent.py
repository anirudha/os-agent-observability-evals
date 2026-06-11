"""OpenAI adapter — tool-calling loop with the Chat Completions API.

Install: pip install "opensearch-genai-observability-sdk-py[openai]"
The [openai] extra auto-instruments the client, so the chat calls below become
`chat` spans automatically; we only add the agent-level enrich() for the model tag.
"""

from __future__ import annotations

import json
import os

from ..observability import enrich
from ..tools import TOOL_FUNCTIONS, TOOL_SCHEMAS, SYSTEM_PROMPT

MODEL = os.environ.get("ACME_MODEL", "gpt-4o")


def _openai_tools():
    return [{"type": "function", "function": s} for s in TOOL_SCHEMAS]


def run_turn(question: str, history: list[dict]) -> str:
    from openai import OpenAI

    client = OpenAI()
    enrich(model=MODEL, provider="openai")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history,
                {"role": "user", "content": question}]

    # Tool-calling loop: keep going until the model stops asking for tools.
    for _ in range(5):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=_openai_tools(),
        )
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return msg.content or ""

        messages.append(msg)
        for call in msg.tool_calls:
            fn = TOOL_FUNCTIONS[call.function.name]
            args = json.loads(call.function.arguments or "{}")
            result = fn(**args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })

    return "Sorry, I couldn't complete that request."
