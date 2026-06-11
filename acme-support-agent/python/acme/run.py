"""CLI runner: python -m acme.run "where is my order #1007?"

Flags:
  --framework  openai | anthropic | bedrock | langchain | llamaindex
  --conversation  conversation id for multi-turn grouping

Examples:
  python -m acme.run "where is my order #1007?"
  python -m acme.run --framework anthropic "is SK-ROCKET in stock?"
  python -m acme.run --framework bedrock "what is your return policy?"
"""

from __future__ import annotations

import argparse

from .observability import setup_observability
from .agent import handle_support_question


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Acme Support Agent.")
    parser.add_argument("question", help="The customer question to answer.")
    parser.add_argument("--framework", default=None,
                        help="openai | anthropic | bedrock | langchain | llamaindex")
    parser.add_argument("--conversation", default="cli-session",
                        help="Conversation id for multi-turn grouping.")
    args = parser.parse_args()

    # Blog Part 3: one call wires up the OTel pipeline.
    setup_observability()

    answer = handle_support_question(
        args.question,
        conversation_id=args.conversation,
        framework=args.framework,
    )
    print(f"\n🤖 {answer}\n")


if __name__ == "__main__":
    main()
