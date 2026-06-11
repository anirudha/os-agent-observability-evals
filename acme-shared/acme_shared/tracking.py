"""Tool-call tracking shared by every variant's eval runner.

The eval suite needs to assert which tools were called for a case (right-tool and
golden-path trajectory checks). The shared tools record their own calls into
acme_shared.tools.CALLS — this works regardless of how an agent framework imported
or wrapped them, which monkey-patching the registry does not.
"""

from __future__ import annotations

from contextlib import contextmanager

from . import tools as tools_mod


def calls() -> list[str]:
    """The tool names called since the last reset()."""
    return list(tools_mod.CALLS)


def reset() -> None:
    tools_mod.CALLS.clear()


def install() -> None:
    """No-op kept for backwards compatibility — tools self-record now."""
    return None


@contextmanager
def track_case():
    """Reset tracking for one eval case; yields the live list of calls."""
    reset()
    yield tools_mod.CALLS
