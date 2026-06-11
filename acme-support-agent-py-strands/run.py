"""Run the Strands Acme agent: python run.py "where is my order #1007?" """

from __future__ import annotations

import argparse

from acme_shared import setup_observability
from strands_agent import handle_support_question


def main() -> None:
    p = argparse.ArgumentParser(description="Acme Support Agent on Strands.")
    p.add_argument("question")
    p.add_argument("--conversation", default="cli-session")
    args = p.parse_args()

    setup_observability(service_name="acme-support-agent")
    answer = handle_support_question(args.question, conversation_id=args.conversation)
    print(f"\n🤖 {answer}\n")


if __name__ == "__main__":
    main()
