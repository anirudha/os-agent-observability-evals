"""Shared eval-run identity + span attributes (Blog Parts 6 & 8).

Every variant's `run_evals` stamps the same `test.*` semantic-convention
attributes + `eval_mode` + `eval_question` onto its evaluation spans, so the
shared dashboards can filter by check / experiment / mode and compare runs
regardless of which framework produced them.
"""
from __future__ import annotations

import datetime
import os
import uuid

DATASET_NAME = "acme-golden-v1"


def new_run_ctx(framework: str) -> dict:
    """Identity for one eval run. ACME_EXPERIMENT overrides the label
    (defaults to the framework name, so the Experiment filter compares frameworks)."""
    run_id = "run-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    experiment = os.environ.get("ACME_EXPERIMENT") or framework
    return {"run_id": run_id, "experiment": experiment, "dataset": DATASET_NAME}


def case_attrs(run_ctx: dict, case, checks: dict | None = None,
               mode: str = "offline", passed: bool | None = None) -> dict:
    """Attributes for every score() call of one case (test.* semconv + eval_mode).

    Pass `passed` explicitly for library judges whose pass threshold isn't `>=1`;
    otherwise it's derived from `checks` (all values `>= 1`)."""
    if passed is None:
        passed = all(v >= 1 for v in (checks or {}).values())
    return {
        "eval_question": case.question,
        "test.suite.run.id": run_ctx["run_id"],
        "test.suite.name": run_ctx["experiment"],
        "test.case.id": case.case_id,
        "test.case.result.status": "pass" if passed else "fail",
        "dataset": run_ctx["dataset"],
        "eval_mode": mode,
    }
