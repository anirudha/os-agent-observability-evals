"""Acme Support Agent on the Strands Agents SDK.

Strands is model-driven: you hand it tools and a system prompt and it runs the
reasoning loop. We wrap the run in an invoke_agent span; the shared tools keep
emitting execute_tool spans. Strands also emits OTel spans natively, so the
OpenSearch SDK's auto-instrumentation and Strands' own telemetry compose.

Install: pip install strands-agents strands-agents-tools
Docs: https://strandsagents.com
"""

from __future__ import annotations

import os

from acme_shared import observe, enrich, Op
from acme_shared.tools import lookup_order, check_inventory, search_policy, SYSTEM_PROMPT

MODEL = os.environ.get("ACME_MODEL", "us.anthropic.claude-3-5-sonnet-20240620-v1:0")


def _build_agent():
    from strands import Agent, tool

    # Wrap the shared Acme tools as Strands @tool functions. Same underlying
    # @observe-decorated functions, so execute_tool spans are still emitted.
    @tool
    def lookup_order_tool(order_id: str) -> dict:
        """Look up the status, items, and ship date of an order by its order ID."""
        return lookup_order(order_id)

    @tool
    def check_inventory_tool(sku: str) -> dict:
        """Check how many units of a SKU are in stock."""
        return check_inventory(sku)

    @tool
    def search_policy_tool(query: str) -> dict:
        """Search Acme's returns and shipping policy for an answer."""
        return search_policy(query)

    return Agent(
        model=MODEL,
        system_prompt=SYSTEM_PROMPT,
        tools=[lookup_order_tool, check_inventory_tool, search_policy_tool],
    )


@observe(op=Op.INVOKE_AGENT, name="acme-support-agent")
def handle_support_question(question: str, conversation_id: str = "anonymous", **_) -> str:
    enrich(provider="strands", session_id=conversation_id)  # session_id -> gen_ai.conversation.id
    agent = _build_agent()
    result = agent(question)
    # Strands returns a result object; its str() is the final text.
    return str(result)
