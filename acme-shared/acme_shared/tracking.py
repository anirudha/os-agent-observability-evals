"""Tool-call tracking shared by every variant's eval runner.

Wraps the shared tools so the eval suite can assert which tools were called for a
case (right-tool and golden-path trajectory checks) without depending on the trace
backend being queryable mid-run.
"""

from __future__ import annotations

from contextlib import contextmanager

from . import tools as tools_mod
from .tools import TOOL_FUNCTIONS

_called: list[str] = []


def calls() -> list[str]:
    """The tool names called since the last reset()."""
    return list(_called)


def reset() -> None:
    _called.clear()


def install() -> None:
    """Patch each shared tool to record its name when called. Idempotent-ish."""
    for name, fn in list(TOOL_FUNCTIONS.items()):
        if getattr(fn, "_acme_tracked", False):
            continue

        def make(orig, tool_name):
            def tracker(*args, **kwargs):
                _called.append(tool_name)
                return orig(*args, **kwargs)
            tracker._acme_tracked = True  # type: ignore[attr-defined]
            return tracker

        wrapped = make(fn, name)
        TOOL_FUNCTIONS[name] = wrapped
        setattr(tools_mod, name, wrapped)


@contextmanager
def track_case():
    """Reset tracking for one eval case; yields the list that fills up."""
    reset()
    yield _called
