"""Shared LangGraph agent builder.

Used by every LangGraph-based variant (plain, +DeepEval, +Ragas). The agent is a
prebuilt ReAct agent over the shared Acme tools, wrapped in an invoke_agent span.
The tools keep emitting execute_tool spans because they're the same
@observe-decorated functions from acme_shared.tools.
"""

from __future__ import annotations

import os

from .observability import observe, enrich, Op
from .tools import lookup_order, check_inventory, search_policy, SYSTEM_PROMPT

# Provider is selectable so the same agent runs on OpenAI or Bedrock.
#   ACME_LLM_PROVIDER=openai  (default)  -> needs langchain-openai + OPENAI_API_KEY
#   ACME_LLM_PROVIDER=bedrock            -> needs langchain-aws + AWS credentials
PROVIDER = os.environ.get("ACME_LLM_PROVIDER", "openai").lower()
_DEFAULT_MODEL = {
    "openai": "gpt-4o",
    "bedrock": "global.anthropic.claude-haiku-4-5-20251001-v1:0",
}.get(PROVIDER, "gpt-4o")
MODEL = os.environ.get("ACME_MODEL", _DEFAULT_MODEL)


def _make_llm():
    if PROVIDER == "bedrock":
        from langchain_aws import ChatBedrockConverse
        return ChatBedrockConverse(model=MODEL, temperature=0)
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=MODEL, temperature=0)


def build_agent():
    from langchain_core.tools import tool
    from langgraph.prebuilt import create_react_agent

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

    llm = _make_llm()
    return create_react_agent(
        llm,
        [lookup_order_tool, check_inventory_tool, search_policy_tool],
        prompt=SYSTEM_PROMPT,
    )


# name= on an INVOKE_AGENT span sets gen_ai.agent.name, so we name it for the agent.
@observe(op=Op.INVOKE_AGENT, name="acme-support-agent")
def handle_support_question(
    question: str,
    conversation_id: str = "anonymous",
    history: list[dict] | None = None,
) -> str:
    """invoke_agent span. chat + execute_tool child spans come from the graph + tools."""
    enrich(model=MODEL, provider=PROVIDER,
           session_id=conversation_id)  # session_id -> gen_ai.conversation.id
    agent = build_agent()
    result = agent.invoke({"messages": [*(history or []), {"role": "user", "content": question}]})
    return result["messages"][-1].content
