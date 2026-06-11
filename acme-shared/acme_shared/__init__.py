"""Shared core for all Acme Support Agent observability variants.

Every variant (LangGraph, Strands, AgentCore, and the eval-library flavors)
imports its tools, observability wiring, dataset, and eval criteria from here so
the only thing that differs per variant is the agent framework and the eval lib.
"""

from .observability import setup_observability, observe, enrich, score, Op
from .tools import (
    lookup_order,
    check_inventory,
    search_policy,
    TOOL_FUNCTIONS,
    TOOL_SCHEMAS,
    SYSTEM_PROMPT,
)
from .dataset import EvalCase, GOLDEN_CASES, full_dataset, load_from_production_traces
from . import criteria

__all__ = [
    "setup_observability", "observe", "enrich", "score", "Op",
    "lookup_order", "check_inventory", "search_policy",
    "TOOL_FUNCTIONS", "TOOL_SCHEMAS", "SYSTEM_PROMPT",
    "EvalCase", "GOLDEN_CASES", "full_dataset", "load_from_production_traces",
    "criteria",
]
