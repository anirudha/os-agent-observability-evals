"""Ragas eval runner for the LangGraph variant.

Same agent, dataset, and golden paths as the LangGraph baseline — judged with
Ragas. Ragas is built around RAG/agent metrics; we use two that fit a tool-using
support agent:

  - AspectCritic("correctness")   (LLM-judged: is the answer correct vs. reference?)
  - ToolCallAccuracy              (did the agent call the expected tools, in order?)

Scores are emitted via score() so they land next to the traces in OpenSearch.

  python -m evals.run_evals
Docs: https://docs.ragas.io/
"""

from __future__ import annotations

import time

from acme_shared import setup_observability, score, full_dataset
from acme_shared import observe, Op, enrich
from acme_shared.tracking import install, track_case
from acme_shared.langgraph_agent import handle_support_question


def _ragas_correctness(case, answer) -> float:
    """LLM-judged correctness via Ragas AspectCritic (binary 0/1)."""
    from ragas import SingleTurnSample
    from ragas.metrics import AspectCritic
    from ragas.llms import LangchainLLMWrapper
    from langchain_openai import ChatOpenAI

    judge = LangchainLLMWrapper(ChatOpenAI(model="gpt-4o", temperature=0))
    metric = AspectCritic(
        name="correctness",
        definition=(
            "Return 1 if the response correctly answers the question and is "
            f"consistent with this expected fact: '{case.expected_answer_substring}'. "
            "Otherwise return 0."
        ),
        llm=judge,
    )
    sample = SingleTurnSample(user_input=case.question, response=answer)
    return float(metric.single_turn_score(sample))


def _tool_accuracy(case, tools_called) -> float:
    """Deterministic tool-call accuracy: expected tool present and path matches."""
    if case.expected_tool not in tools_called:
        return 0.0
    actual_traj = ["invoke_agent", *tools_called]
    return 1.0 if actual_traj[: len(case.golden_trajectory)] == case.golden_trajectory else 0.5


@observe(op=Op.INVOKE_AGENT, name="eval_case")
def run_case(case) -> dict:
    enrich(eval_question=case.question, expected_tool=case.expected_tool, eval_lib="ragas")
    with track_case() as called:
        start = time.time()
        answer = handle_support_question(case.question, conversation_id=case.conversation_id)
        elapsed = time.time() - start
        called = list(called)

    correctness = _ragas_correctness(case, answer)
    tool_accuracy = _tool_accuracy(case, called)

    score(name="ragas.correctness", value=correctness)
    score(name="ragas.tool_call_accuracy", value=tool_accuracy)

    passed = correctness >= 0.99 and tool_accuracy >= 0.99
    return {"question": case.question, "answer": answer, "tools": called,
            "correctness": correctness, "tool_accuracy": tool_accuracy,
            "latency_s": round(elapsed, 2), "passed": passed}


def main() -> None:
    setup_observability(service_name="acme-support-agent")
    install()
    results = [run_case(c) for c in full_dataset()]
    passed = sum(r["passed"] for r in results)
    print("\n" + "=" * 72)
    print(f"  ACME EVAL (LangGraph + Ragas) — {passed}/{len(results)} passed")
    print("=" * 72)
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark}  {r['question']}")
        print(f"      correctness={r['correctness']:.2f}  "
              f"tool_accuracy={r['tool_accuracy']:.2f}  tools={r['tools']}  {r['latency_s']}s")
    print("=" * 72)
    print("Ragas scores are emitted as score() -> query them beside traces in OpenSearch.\n")


if __name__ == "__main__":
    main()
