"""Eval runner for the AgentCore variant.

Calls the same entrypoint logic the deployed runtime serves, so you evaluate the
exact code path that runs in production. Native-SDK scoring, same dataset and golden
paths as every other variant.

  python -m evals.run_evals
"""

from __future__ import annotations

import time

from acme_shared import setup_observability, score, full_dataset, criteria
from acme_shared import observe, Op, enrich
from acme_shared.tracking import install, track_case
from acme_shared.evalmeta import new_run_ctx, case_attrs

# Import the entrypoint's underlying agent function (no HTTP server needed for evals).
from agent import _run_agent


@observe(op=Op.INVOKE_AGENT, name="eval_case")
def run_case(case, run_ctx) -> dict:
    enrich(eval_question=case.question, expected_tool=case.expected_tool)
    with track_case() as called:
        start = time.time()
        answer = _run_agent(case.question, case.conversation_id)
        elapsed = time.time() - start
        called = list(called)

    correctness = criteria.judge_answer_correctness(case.question, answer, case.expected_answer_substring)
    right_tool = 1.0 if case.expected_tool in called else 0.0
    actual_traj = ["invoke_agent", *called]
    trajectory = 1.0 if actual_traj[: len(case.golden_trajectory)] == case.golden_trajectory else 0.0
    latency_ok = criteria.judge_latency(elapsed)

    checks = {"answer_correctness": correctness, "right_tool": right_tool,
              "trajectory_match": trajectory, "latency_ok": latency_ok}
    common = case_attrs(run_ctx, case, checks)
    for name, value in checks.items():
        score(name=name, value=value, attributes=common)
    enrich(**{"test.suite.run.id": run_ctx["run_id"], "test.suite.name": run_ctx["experiment"],
              "eval_mode": "offline"})

    return {"question": case.question, "answer": answer, "tools": called,
            "correctness": correctness, "trajectory": trajectory,
            "latency_s": round(elapsed, 2),
            "passed": all([correctness, right_tool, trajectory, latency_ok])}


def main() -> None:
    setup_observability(service_name="acme-support-agent")
    install()
    run_ctx = new_run_ctx("agentcore")
    print(f"  run_id={run_ctx['run_id']}  experiment={run_ctx['experiment']}  dataset={run_ctx['dataset']}")
    results = [run_case(c, run_ctx) for c in full_dataset()]
    passed = sum(r["passed"] for r in results)
    print("\n" + "=" * 72)
    print(f"  ACME EVAL (AgentCore Runtime) — {passed}/{len(results)} passed")
    print("=" * 72)
    for r in results:
        mark = "✅" if r["passed"] else "❌"
        print(f"{mark}  {r['question']}  tools={r['tools']}  "
              f"correct={r['correctness']:.0f}  traj={r['trajectory']:.0f}  {r['latency_s']}s")
    print("=" * 72 + "\n")


if __name__ == "__main__":
    main()
