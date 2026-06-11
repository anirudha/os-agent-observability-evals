# OpenSearch AI Agent Observability & Evals

A hands-on tutorial and runnable example for instrumenting, observing, and
**evaluating** AI agents with the [OpenSearch AI observability stack](https://observability.opensearch.org/docs/ai-observability/).

It meets you wherever you are — building a new agent, iterating in dev, or running
one in production — and on whatever framework you already use, then walks the full
journey to a **healthy production agent**:

> **instrument → verify → observe → evaluate → monitor → close the loop**

## What's here

| Path | What it is |
|---|---|
| [`blog.md`](blog.md) | The tutorial walkthrough — read this first |
| [`acme-support-agent/`](acme-support-agent/) | The runnable companion repo: a full example agent + the local stack |

## The example: Acme Support Agent

One example agent threaded through every step so you can follow it end to end. It's a
customer-support bot for a fictional store, with three deterministic tools
(`lookup_order`, `check_inventory`, `search_policy`) — chosen so evaluation is
**objective** and there's a clear **golden path** for trajectory comparison.

It exercises every span type the stack cares about: `invoke_agent` → `chat` →
`execute_tool` → `retrieval` / `embeddings`. The agent logic and observability code
are written **once**; only the model/tool-calling layer swaps per framework.

## Frameworks covered

The main tutorial ([`acme-support-agent/`](acme-support-agent/)) shows every framework
in one repo:

| Runtime | Frameworks | Path |
|---|---|---|
| **Python** | OpenAI · Anthropic · Bedrock · LangChain · LlamaIndex | native SDK (`opensearch-genai-observability-sdk-py`) |
| **TypeScript** | raw OpenTelemetry (native JS SDK [in development](https://github.com/opensearch-project/genai-observability-sdk-js)) | manual `gen_ai.*` spans |

## Standalone variants

Each variant is a focused, runnable flow for one framework or eval library. They all
share one core ([`acme-shared/`](acme-shared/) — tools, observability, dataset, golden
paths, criteria), so the **only** thing that differs is the agent framework or the eval
layer. That makes them apples-to-apples on the same dataset.

| Variant | Framework | Eval layer |
|---|---|---|
| [`acme-support-agent-py-langgraph`](acme-support-agent-py-langgraph/) | LangGraph | native SDK `score()` |
| [`acme-support-agent-py-strands`](acme-support-agent-py-strands/) | [Strands Agents](https://strandsagents.com) | native SDK `score()` |
| [`acme-support-agent-py-langgraph-deepeval`](acme-support-agent-py-langgraph-deepeval/) | LangGraph | [DeepEval](https://docs.confident-ai.com/) → `score()` |
| [`acme-support-agent-py-langgraph-ragas`](acme-support-agent-py-langgraph-ragas/) | LangGraph | [Ragas](https://docs.ragas.io/) → `score()` |
| [`acme-support-agent-agentcore`](acme-support-agent-agentcore/) | [Bedrock AgentCore Runtime](https://aws.amazon.com/bedrock/agentcore/) | native SDK `score()` |

Every variant emits its eval scores via `score()`, so results land beside the traces in
OpenSearch regardless of which eval library produced them. Each folder has its own
README with setup and run steps.

## Quick start

```bash
# 1. clone
git clone https://github.com/anirudha/os-agent-observability-evals.git
cd os-agent-observability-evals/acme-support-agent

# 2. bring up the stack (OpenSearch, OTel Collector, Data Prepper, Prometheus, Dashboards)
docker compose up -d
./verify/check-stack.sh

# 3. run the agent on your framework
cd python
pip install -e ".[openai]"          # or [anthropic], [bedrock], [langchain], [llamaindex], [all]
export OPENAI_API_KEY=sk-...
python -m acme.run "where is my order #1007?"

# 4. confirm telemetry landed, then run the eval suite
cd .. && ./verify/check-instrumentation.sh
cd python && python -m evals.run_evals
```

Explore the traces in OpenSearch Dashboards at http://localhost:5601
(`admin` / `My_password_123!@#`).

See [`acme-support-agent/README.md`](acme-support-agent/README.md) for the full
repo layout, per-part mapping, and details.

## The journey

Full index with read / code / run links for every part:
**[`acme-support-agent/docs/README.md`](acme-support-agent/docs/README.md)**.

| Part | Step | In the repo |
|---|---|---|
| 1 | Define goals → eval criteria | [`python/evals/criteria.py`](acme-support-agent/python/evals/criteria.py) |
| 2 | Stand up the stack | [`docker-compose.yml`](acme-support-agent/docker-compose.yml) |
| 3 | Instrument your framework | [`python/acme/observability.py`](acme-support-agent/python/acme/observability.py), [`typescript/src/observability.ts`](acme-support-agent/typescript/src/observability.ts) |
| 4 | Verify telemetry lands | [`verify/`](acme-support-agent/verify/) |
| 5 | Observe & debug | [`verify/queries.md`](acme-support-agent/verify/queries.md) |
| 6 | Evaluate against a dataset | [`python/evals/`](acme-support-agent/python/evals/) |
| 7 | Monitor production | [`infra/prometheus/`](acme-support-agent/infra/prometheus/), [`docs/production.md`](acme-support-agent/docs/production.md) |
| 8 | Close the loop | [`python/evals/dataset.py`](acme-support-agent/python/evals/dataset.py) |

## A note on credentials

The local stack uses default OpenSearch credentials and skips TLS verification —
**local development only.** For the AWS-managed path (Amazon OpenSearch Service +
Amazon Managed Prometheus with SigV4), see
[`acme-support-agent/docs/production.md`](acme-support-agent/docs/production.md).
