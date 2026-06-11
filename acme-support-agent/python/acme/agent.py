"""The Acme agent entry point.

`handle_support_question` is the top-level span (invoke_agent). It enriches the
trace with the conversation id and model, then delegates the tool-calling loop to
the selected framework adapter. This single function is what every part of the
tutorial — observe, evaluate, monitor — hangs off of.
"""

from __future__ import annotations

from .observability import observe, enrich, Op
from .frameworks import get_adapter


# name= on an INVOKE_AGENT span sets gen_ai.agent.name.
@observe(op=Op.INVOKE_AGENT, name="acme-support-agent")
def handle_support_question(
    question: str,
    conversation_id: str = "anonymous",
    history: list[dict] | None = None,
    framework: str | None = None,
) -> str:
    """Answer one customer support question.

    This is the invoke_agent span. The chat + execute_tool child spans are
    emitted by the framework adapter and the @observe-decorated tools.
    """
    enrich(session_id=conversation_id)  # session_id -> gen_ai.conversation.id
    run_turn = get_adapter(framework)
    return run_turn(question, history or [])
