"""DeepEval eval runner for the LangGraph variant.

Same agent, dataset, and golden paths as the LangGraph baseline — but the judging
layer is DeepEval. We run two DeepEval metrics:

  - AnswerRelevancyMetric        (LLM-as-judge: is the answer relevant/correct?)
  - ToolCorrectnessMetric        (did the agent call the expected tools?)

DeepEval's scores are then emitted as score() calls so they live next to the traces
in OpenSearch instead of in a separate silo — that's the whole point of pairing an
external eval lib with the observability stack.

  python -m evals.run_evals
Docs: https://docs.confident-ai.com/
"""

from __future__ import annotations

import time

from acme_shared import setup_observability, score, full_dataset
from acme_shared import observe, Op, enrich
from acme_shared.tracking import install, track_case
from acme_shared.langgraph_agent import handle_support_question


def _judge_model():
    """Pick the LLM DeepEval uses to judge.

    DeepEval defaults to OpenAI. Set DEEPEVAL_JUDGE=bedrock to judge with a
    Bedrock model instead (no OpenAI key needed) — handy on AWS-only setups.
    """
    import os

    if os.environ.get("DEEPEVAL_JUDGE", "").lower() == "bedrock":
        from deepeval.models import AmazonBedrockModel
        return AmazonBedrockModel(
            model=os.environ.get("DEEPEVAL_JUDGE_MODEL",
                                 "global.anthropic.claude-haiku-4-5-20251001-v1:0"),
            region=os.environ.get("AWS_REGION", "us-east-1"),
        )
    return None  # DeepEval uses its OpenAI default


def _deepeval_score(case, answer, tools_called):
    """Run DeepEval metrics and return a dict of metric_name -> score."""
    from deepeval.test_case import LLMTestCase, ToolCall
    from deepeval.metrics import AnswerRelevancyMetric, ToolCorrectnessMetric

    test_case = LLMTestCase(
        input=case.question,
        actual_output=answer,
        expected_output=case.expected_answer_substring,
        tools_called=[ToolCall(name=t) for t in tools_called],
        expected_tools=[ToolCall(name=case.expected_tool)],
    )

    judge = _judge_model()
    # Pass the judge to both metrics. AnswerRelevancy uses it to score; recent
    # DeepEval versions also initialize a model on ToolCorrectnessMetric even
    # though its scoring is deterministic, so it needs one too.
    if judge:
        relevancy = AnswerRelevancyMetric(threshold=0.7, model=judge)
        tool_correctness = ToolCorrectnessMetric(model=judge)
    else:
        relevancy = AnswerRelevancyMetric(threshold=0.7)
        tool_correctness = ToolCorrectnessMetric()

    relevancy.measure(test_case)
    tool_correctness.measure(test_case)

    return {
        "answer_relevancy": float(relevancy.score or 0.0),
        "tool_correctness": float(tool_correctness.score or 0.0),
    }


@observe(op=Op.INVOKE_AGENT, name="eval_case")
def run_case(case) -> dict:
    enrich(eval_question=case.question, expected_tool=case.expected_tool, eval_lib="deepeval")
    with track_case() as called:
        start = time.time()
        answer = handle_support_question(case.question, conversation_id=case.conversation_id)
        elapsed = time.time() - start
        called = list(called)

    scores = _deepeval_score(case, answer, called)
    # emit DeepEval scores onto the trace
    for name, value in scores.items():
        score(name=f"deepeval.{name}", value=value)

    passed = scores["answer_relevancy"] >= 0.7 and scores["tool_correctness"] >= 0.99
    return {"question": case.question, "answer": answer, "tools": called,
            "scores": scores, "latency_s": round(elapsed, 2), "passed": passed}


def main() -> None:
    setup_observability(service_name="acme-support-agent")
    install()
    results = [run_case(c) for c in full_dataset()]
    passed = sum(r["passed"] for r in results)
    print("\n" + "=" * 72)
    print(f"  ACME EVAL (LangGraph + DeepEval) — {passed}/{len(results)} passed")
    print("=" * 72)
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        s = r["scores"]
        print(f"{mark}  {r['question']}")
        print(f"      relevancy={s['answer_relevancy']:.2f}  "
              f"tool_correctness={s['tool_correctness']:.2f}  tools={r['tools']}  {r['latency_s']}s")
    print("=" * 72)
    print("DeepEval scores are emitted as score() -> query them beside traces in OpenSearch.\n")


if __name__ == "__main__":
    main()
