"""Eval criteria — Blog Part 1, "define goals first."

Each goal from the blog becomes a concrete, checkable criterion here. Some are
deterministic (right tool, no loops); the answer-correctness one is where an
LLM-as-judge would plug in. We keep a simple substring judge as the default so the
suite runs with no extra dependencies, and show where to swap in a real judge.
"""

from __future__ import annotations


# Goal -> criterion mapping (mirrors the table in blog Part 1).
GOALS = {
    "answer_correctness": "Final answer contains the expected fact.",
    "right_tool": "Agent called the expected tool for the question.",
    "cost": "Total tokens stayed under budget.",
    "latency": "Answer returned under the latency budget.",
    "no_loops": "Agent did not exceed the max reasoning steps.",
}

TOKEN_BUDGET = 4000          # per request
LATENCY_BUDGET_S = 8.0       # per request
MAX_CHAT_STEPS = 3           # more than this is a loop


def judge_answer_correctness(question: str, answer: str, expected_substring: str) -> float:
    """Default judge: substring match, case-insensitive.

    Swap this for an LLM-as-judge in production, e.g.:

        from openai import OpenAI
        client = OpenAI()
        verdict = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": JUDGE_PROMPT.format(...)}],
        )
        return parse_score(verdict)
    """
    if not answer:
        return 0.0
    return 1.0 if expected_substring.lower() in answer.lower() else 0.0


def judge_no_loops(chat_step_count: int) -> float:
    return 1.0 if chat_step_count <= MAX_CHAT_STEPS else 0.0


def judge_cost(total_tokens: int) -> float:
    return 1.0 if total_tokens <= TOKEN_BUDGET else 0.0


def judge_latency(seconds: float) -> float:
    return 1.0 if seconds <= LATENCY_BUDGET_S else 0.0
