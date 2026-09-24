"""Offline mock agent shared by every variant.

When ACME_MOCK is set, each variant's `handle_support_question` delegates here
instead of calling its real framework/model. Routing goes through the same
`TOOL_FUNCTIONS` registry as the real tools, so `execute_tool` (and the
`retrieval`/`embeddings` children of `search_policy`) spans are still emitted;
the "model turn" is a deterministic `chat` span. No provider or credentials
needed. Token usage is not recorded — matching the variants' real behavior
(only the Bedrock adapter reports tokens today).
"""
from __future__ import annotations

import re

from .observability import observe, enrich, Op
from .tools import TOOL_FUNCTIONS

_NUMBER_RE = re.compile(r"\d{3,}")
_SKU_RE = re.compile(r"[A-Z]{2,}-[A-Z0-9]+")


def _route_and_call(question: str) -> tuple[str, dict]:
    """Pick a tool for the question and call it via TOOL_FUNCTIONS[name]."""
    q = question.lower()
    number = _NUMBER_RE.search(question)
    if "order" in q or number:
        return "lookup_order", TOOL_FUNCTIONS["lookup_order"](number.group(0) if number else "")
    sku = _SKU_RE.search(question)
    if sku or "stock" in q or "inventory" in q:
        return "check_inventory", TOOL_FUNCTIONS["check_inventory"](sku.group(0) if sku else "")
    return "search_policy", TOOL_FUNCTIONS["search_policy"](question)


def _answer_from(tool_name: str, result: dict, question: str) -> str:
    if isinstance(result, dict) and result.get("error"):
        return f"Sorry, I couldn't find an answer to {question!r}."
    if tool_name == "lookup_order":
        answer = f"Your order is {result['status']}."
        if result.get("items"):
            answer += f" Items: {', '.join(result['items'])}."
        if result.get("ship_date"):
            answer += f" Ship date: {result['ship_date']}."
        return answer
    if tool_name == "check_inventory":
        return f"In stock: {result['in_stock']} units."
    return result["answer"]


@observe(op=Op.CHAT, name="mock-chat")
def _mock_chat(question: str) -> str:
    tool_name, result = _route_and_call(question)
    return _answer_from(tool_name, result, question)


def run_turn(question: str) -> str:
    """The offline 'model turn' (a chat span + tool calls), WITHOUT its own
    invoke_agent span — for a variant whose already-decorated
    handle_support_question delegates here so only one invoke_agent is emitted."""
    return _mock_chat(question)


@observe(op=Op.INVOKE_AGENT, name="acme-support-agent")
def handle_support_question(question: str, conversation_id: str = "anonymous", **_) -> str:
    """Standalone offline invoke_agent span (used directly, e.g. from run.py)."""
    enrich(model="mock", provider="mock", session_id=conversation_id)
    return _mock_chat(question)
