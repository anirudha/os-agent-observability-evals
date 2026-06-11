"""LangChain adapter — a tool-calling agent built with LangGraph's prebuilt ReAct agent.

Install: pip install "opensearch-genai-observability-sdk-py[langchain]"
         pip install langchain-openai langgraph
The [langchain] extra registers the callback handler automatically, so the chain's
LLM and tool steps become spans without extra wiring.
"""

from __future__ import annotations

import os

from ..observability import enrich
from ..tools import lookup_order, check_inventory, search_policy, SYSTEM_PROMPT

MODEL = os.environ.get("ACME_MODEL", "gpt-4o")


def _build_agent():
    from langchain_core.tools import tool
    from langchain_openai import ChatOpenAI
    from langgraph.prebuilt import create_react_agent

    # Wrap the shared Acme tools as LangChain tools. They keep emitting
    # execute_tool spans because they're the same @observe-decorated functions.
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


def run_turn(question: str, history: list[dict]) -> str:
    enrich(model=MODEL, provider="openai")
    agent = _build_agent()
    result = agent.invoke({"messages": [*history, {"role": "user", "content": question}]})
    return result["messages"][-1].content
