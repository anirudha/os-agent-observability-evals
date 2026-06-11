"""Observability wiring for the Acme agent.

This is the ONLY file that touches the OpenSearch GenAI SDK directly. Everything
else in the agent imports `observe`, `enrich`, `score`, and `Op` from here, so the
agent code stays clean and the integration lives in one place.

Blog Part 3 (Instrument): one register() call configures the whole OTel pipeline.

We import from the SDK if it is installed, and fall back to no-op shims if it is
not — so the tutorial code still runs (just without telemetry) before you
`pip install opensearch-genai-observability-sdk-py`.
"""

from __future__ import annotations

import os
import functools

_SDK_AVAILABLE = False

try:
    from opensearch_genai_observability_sdk_py import (  # type: ignore
        register as _register,
        observe as _observe,
        enrich as _enrich,
        score as _score,
        Op as _Op,
    )

    _SDK_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback path
    _register = _observe = _enrich = _score = None  # type: ignore
    _Op = None  # type: ignore


# ---------------------------------------------------------------------------
# Op constants — re-exported so the rest of the agent doesn't import the SDK.
# ---------------------------------------------------------------------------

class _OpShim:
    INVOKE_AGENT = "invoke_agent"
    EXECUTE_TOOL = "execute_tool"
    CHAT = "chat"
    RETRIEVAL = "retrieval"
    EMBEDDINGS = "embeddings"


Op = _Op if _SDK_AVAILABLE else _OpShim


# ---------------------------------------------------------------------------
# register() — call once at startup.
# ---------------------------------------------------------------------------

def setup_observability(service_name: str = "acme-support-agent") -> None:
    """Configure the OTel pipeline. Idempotent enough for tutorial use."""
    if not _SDK_AVAILABLE:
        print("[observability] SDK not installed — running without telemetry. "
              "pip install 'opensearch-genai-observability-sdk-py[all]' to enable.")
        return

    endpoint = os.environ.get(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        "http://localhost:4318/v1/traces",
    )
    _register(
        endpoint=endpoint,
        service_name=os.environ.get("OTEL_SERVICE_NAME", service_name),
        # auto_instrument=True by default — discovers installed instrumentors
        # (openai, anthropic, bedrock, langchain, llamaindex, ...)
    )
    print(f"[observability] registered -> {endpoint}")


# ---------------------------------------------------------------------------
# observe / enrich / score — thin wrappers that no-op without the SDK.
# ---------------------------------------------------------------------------

def observe(op=None, name: str | None = None):
    """Decorator: trace a function as a span of the given Op."""
    if _SDK_AVAILABLE:
        return _observe(op=op, name=name) if name else _observe(op=op)

    def _decorator(fn):
        @functools.wraps(fn)
        def _wrapped(*args, **kwargs):
            return fn(*args, **kwargs)
        return _wrapped

    return _decorator


def enrich(**attributes) -> None:
    """Attach gen_ai.* semantic-convention attributes to the active span."""
    if _SDK_AVAILABLE:
        _enrich(**attributes)


def score(name: str, value: float, **kwargs) -> None:
    """Attach an evaluation score to the active trace."""
    if _SDK_AVAILABLE:
        _score(name=name, value=value, **kwargs)
    else:
        print(f"[score] {name}={value}")
