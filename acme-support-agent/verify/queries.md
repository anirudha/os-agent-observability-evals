# Observe & debug — PPL query cookbook (Blog Part 5)

Copy-paste PPL queries for exploring the Acme agent's traces. All use the local
stack defaults (`admin` / `My_password_123!@#`, `-k` to skip TLS verification).
Run them via the PPL API or paste the query body into OpenSearch Dashboards →
Observability → PPL.

Set these once:

```bash
OS=https://localhost:9200
AUTH='admin:My_password_123!@#'
ppl() { curl -sk -u "$AUTH" -X POST "$OS/_plugins/_ppl" -H 'Content-Type: application/json' -d "{\"query\": \"$1\"}"; }
```

## Reconstruct one trace (the full reasoning tree)

```bash
ppl "source=otel-v1-apm-span-* | where traceId = '<TRACE_ID>' | fields spanId, parentSpanId, name, \`attributes.gen_ai.operation.name\`, durationInNanos | sort startTime"
```

## Recent agent invocations

```bash
ppl "source=otel-v1-apm-span-* | where \`attributes.gen_ai.operation.name\` = 'invoke_agent' | fields traceId, \`attributes.gen_ai.agent.name\`, durationInNanos, startTime | sort - startTime | head 20"
```

## Slow agent invocations (> 5s)

```bash
ppl "source=otel-v1-apm-span-* | where \`attributes.gen_ai.operation.name\` = 'invoke_agent' AND durationInNanos > 5000000000 | fields traceId, \`attributes.gen_ai.agent.name\`, durationInNanos | sort - durationInNanos"
```

## Error spans (status.code = 2 is ERROR in OTel)

```bash
ppl "source=otel-v1-apm-span-* | where \`status.code\` = 2 | fields traceId, serviceName, name, \`events.attributes.exception.message\` | sort - startTime | head 20"
```

## Token usage by model (cost signal)

```bash
ppl "source=otel-v1-apm-span-* | where \`attributes.gen_ai.usage.input_tokens\` > 0 | stats sum(\`attributes.gen_ai.usage.input_tokens\`) as in_tokens, sum(\`attributes.gen_ai.usage.output_tokens\`) as out_tokens by \`attributes.gen_ai.request.model\`"
```

## Tool call inspection (arguments + results)

```bash
ppl "source=otel-v1-apm-span-* | where \`attributes.gen_ai.operation.name\` = 'execute_tool' | fields \`attributes.gen_ai.tool.name\`, \`attributes.gen_ai.tool.call.arguments\`, \`attributes.gen_ai.tool.call.result\`, durationInNanos | sort - startTime | head 20"
```

## Multi-turn conversation tracking

```bash
ppl "source=otel-v1-apm-span-* | where \`attributes.gen_ai.conversation.id\` != '' | stats count() as turns, sum(\`attributes.gen_ai.usage.input_tokens\`) as in_tokens by \`attributes.gen_ai.conversation.id\`"
```

## Eval scores (Blog Part 6) — find low-scoring runs

```bash
# score() emits scores onto spans; adjust the field name to match your SDK version
ppl "source=otel-v1-apm-span-* | where \`attributes.gen_ai.operation.name\` = 'invoke_agent' | fields traceId, \`attributes.eval.answer_correctness\`, \`attributes.eval.trajectory_match\` | sort startTime"
```

## Detect the "looped & hallucinated" failure mode

A trace with multiple `chat` spans and no `execute_tool` is the classic bad case:

```bash
ppl "source=otel-v1-apm-span-* | stats count(eval(\`attributes.gen_ai.operation.name\`='chat')) as chats, count(eval(\`attributes.gen_ai.operation.name\`='execute_tool')) as tools by traceId | where chats > 2 AND tools = 0"
```
