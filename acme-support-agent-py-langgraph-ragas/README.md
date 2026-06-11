# Acme Support Agent — LangGraph + Ragas

Same LangGraph agent as [`../acme-support-agent-py-langgraph`](../acme-support-agent-py-langgraph),
evaluated with **[Ragas](https://docs.ragas.io/)**. Ragas' scores are emitted via
`score()` so they land beside the traces in OpenSearch.

## Metrics

| Ragas metric | What it checks |
|---|---|
| `AspectCritic("correctness")` | LLM-judged: is the answer correct vs. the expected fact? |
| tool-call accuracy | did the agent call the expected tool, on the golden path? |

## Setup

Bring up the stack from [`../acme-support-agent`](../acme-support-agent)
(`docker compose up -d`), then:

```bash
pip install -e ../acme-shared
pip install -e .
export OPENAI_API_KEY=sk-...     # used by the agent and the Ragas judge
```

## Run

```bash
python run.py "where is my order #1007?"
python -m evals.run_evals
```

## Why two eval-library variants?

[`-deepeval`](../acme-support-agent-py-langgraph-deepeval) and `-ragas` run the
**identical agent and dataset** through different eval libraries. Comparing them shows
how each library frames correctness and tool-use — and that, either way, the scores
end up next to your traces in OpenSearch via `score()`.
