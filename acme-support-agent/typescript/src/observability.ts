/**
 * Observability setup — Blog Part 3b (TypeScript).
 *
 * Uses the OpenSearch GenAI Observability SDK for TypeScript:
 *   https://github.com/opensearch-project/genai-observability-sdk-ts
 *   npm: @opensearch-project/genai-observability-sdk-ts
 *
 * register() configures the OTel pipeline — same model as the Python SDK.
 * Import this module FIRST (via --import) so the SDK starts before the agent runs.
 */

import { register } from "@opensearch-project/genai-observability-sdk-ts";

await register({
  endpoint:
    process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT ??
    "http://localhost:4318/v1/traces",
  serviceName: process.env.OTEL_SERVICE_NAME ?? "acme-support-agent",
  // autoInstrument discovers installed instrumentors (e.g. @opentelemetry/instrumentation-openai)
  batch: false,
});

console.log("[observability] register() complete");
