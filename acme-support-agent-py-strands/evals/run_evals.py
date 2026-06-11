"""Native-SDK eval runner for the Strands variant.

Identical scoring to the LangGraph baseline — only the agent under test differs —
so you can compare frameworks on the same dataset and golden paths.

  python -m evals.run_evals
"""

from __future__ import annotations

import time

from acme_shared import setup_observability, score, full_dataset, criteria
from acme_shared import observe, Op, enrich
from acme_shared.tracking import install, track_case
from strands_agent import handle_support_question


@observe(op=Op.INVOKE_AGENT, name="eval_case")
def run_case(case) -> dict:
    enrich(eval_question=case.question, expected_tool=case.expected_tool)
    with track_case() as called:
        start = time.time()
        answer = handle_support_question(case.question, conversation_id=case.conversation_id)
        elapsed = time.time() - start
        called = list(called)

    correctness = criteria.judge_answer_correctness(case.question, answer, case.expected_answer_substring)
    right_tool = 1.0 if case.expected_tool in called else 0.0
    actual_traj = ["invoke_agent", *called]
    trajectory = 1.0 if actual_traj[: len(case.golden_trajectory)] == case.golden_trajectory else 0.0
    latency_ok = criteria.judge_latency(elapsed)

    for name, value in [
        ("answer_correctness", correctness), ("right_tool", right_tool),
        ("trajectory_match", trajectory), ("latency_ok", latency_ok),
    ]:
        score(name=name, value=value)

    return {
        "question": case.question, "answer": answer, "tools": called,
        "correctness": correctness, "trajectory": trajectory,
        "latency_s": round(elapsed, 2),
        "passed": all([correctness, right_tool, trajectory, latency_ok]),
    }


def main() -> None:
    setup_observability(service_name="acme-support-agent")
    install()
    results = [run_case(c) for c in full_dataset()]
    passed = sum(r["passed"] for r in results)
    print("\n" + "=" * 72)
    print(f"  ACME EVAL (Strands, native SDK) — {passed}/{len(results)} passed")
    print("=" * 72)
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark}  {r['question']}  tools={r['tools']}  "
              f"correct={r['correctness']:.0f}  traj={r['trajectory']:.0f}  {r['latency_s']}s")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
