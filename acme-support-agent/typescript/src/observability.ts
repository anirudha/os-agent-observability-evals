/**
 * Observability setup — Blog Part 3b (TypeScript interim path).
 *
 * The native OpenSearch JS GenAI SDK is under active development:
 *   https://github.com/opensearch-project/genai-observability-sdk-js
 * Until it ships, we use standard OpenTelemetry with manual gen_ai.* attributes
 * so spans land in the same otel-v1-apm-* indices as the Python path.
 *
 * Import this module FIRST (via --import) so the SDK starts before the agent runs.
 */

import { NodeSDK } from "@opentelemetry/sdk-node";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";

const endpoint =
  process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT ??
  "http://localhost:4318/v1/traces";

const sdk = new NodeSDK({
  serviceName: process.env.OTEL_SERVICE_NAME ?? "acme-support-agent",
  traceExporter: new OTLPTraceExporter({ url: endpoint }),
});

sdk.start();
console.log(`[observability] OTel started -> ${endpoint}`);

process.on("SIGTERM", () => sdk.shutdown().finally(() => process.exit(0)));
