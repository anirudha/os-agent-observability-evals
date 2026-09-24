"""Offline-mode flag, shared by every variant.

Set ACME_MOCK=1 to run any variant fully offline — deterministic canned answers
stand in for the real framework/model call, but the same
invoke_agent → chat → execute_tool → retrieval/embeddings span chain still lands
in OpenSearch. Mirrors the main tutorial agent's ACME_MOCK so the standalone
variants honor the blog's "no provider account" promise too.
"""
from __future__ import annotations
import os


def mock_enabled() -> bool:
    return os.environ.get("ACME_MOCK", "").lower() in ("1", "true", "yes")
