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

MODEL = os.environ.get("ACME_MODEL", "gpt-4o")


def build_agent():
    from langchain_core.tools import tool
    from langchain_openai import ChatOpenAI
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

    llm = ChatOpenAI(model=MODEL, temperature=0)
    return create_react_agent(
        llm,
        [lookup_order_tool, check_inventory_tool, search_policy_tool],
        prompt=SYSTEM_PROMPT,
    )


@observe(op=Op.INVOKE_AGENT, name="handle_support_question")
def handle_support_question(
    question: str,
    conversation_id: str = "anonymous",
    history: list[dict] | None = None,
) -> str:
    """invoke_agent span. chat + execute_tool child spans come from the graph + tools."""
    enrich(agent_name="acme-support-agent", conversation_id=conversation_id)
    agent = build_agent()
    result = agent.invoke({"messages": [*(history or []), {"role": "user", "content": question}]})
    return result["messages"][-1].content
