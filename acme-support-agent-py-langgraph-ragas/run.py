"""Run the LangGraph Acme agent (Ragas variant shares the same agent).

  python run.py "where is my order #1007?"
"""

from __future__ import annotations

import argparse

from acme_shared import setup_observability
from acme_shared.langgraph_agent import handle_support_question


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("question")
    p.add_argument("--conversation", default="cli-session")
    args = p.parse_args()
    setup_observability(service_name="acme-support-agent")
    print(f"\n🤖 {handle_support_question(args.question, conversation_id=args.conversation)}\n")


if __name__ == "__main__":
    main()
