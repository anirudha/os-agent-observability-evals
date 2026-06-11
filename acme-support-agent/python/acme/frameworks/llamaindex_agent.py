"""LlamaIndex adapter — a FunctionAgent / ReActAgent over the shared Acme tools.

Install: pip install "opensearch-genai-observability-sdk-py[llamaindex]"
         pip install llama-index llama-index-llms-openai
"""

from __future__ import annotations

import os

from ..observability import enrich
from ..tools import lookup_order, check_inventory, search_policy, SYSTEM_PROMPT

MODEL = os.environ.get("ACME_MODEL", "gpt-4o")


def _build_agent():
    from llama_index.core.tools import FunctionTool
    from llama_index.core.agent import ReActAgent
    from llama_index.llms.openai import OpenAI

    tools = [
        FunctionTool.from_defaults(fn=lookup_order, name="lookup_order"),
        FunctionTool.from_defaults(fn=check_inventory, name="check_inventory"),
        FunctionTool.from_defaults(fn=search_policy, name="search_policy"),
    ]
    llm = OpenAI(model=MODEL, temperature=0)
    return ReActAgent.from_tools(tools, llm=llm, system_prompt=SYSTEM_PROMPT, verbose=False)


def run_turn(question: str, history: list[dict]) -> str:
    enrich(model=MODEL, provider="openai")
    agent = _build_agent()
    response = agent.chat(question)
    return str(response)
