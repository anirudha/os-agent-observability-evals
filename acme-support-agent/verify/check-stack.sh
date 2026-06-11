#!/usr/bin/env bash
# Blog Part 2/4: verify the local stack is up and healthy.
set -euo pipefail

OS_URL="${OPENSEARCH_URL:-https://localhost:9200}"
OS_USER="${OPENSEARCH_USERNAME:-admin}"
OS_PASS="${OPENSEARCH_PASSWORD:-My_password_123!@#}"

echo "==> OpenSearch cluster health"
curl -sk -u "$OS_USER:$OS_PASS" "$OS_URL/_cluster/health?pretty" \
  | grep -E '"status"' || { echo "❌ OpenSearch unreachable"; exit 1; }

echo "==> Prometheus health"
curl -s http://localhost:9090/-/healthy || { echo "❌ Prometheus unreachable"; exit 1; }
echo

echo "==> OTel Collector internal metrics (receiver accepted spans)"
curl -s http://localhost:8888/metrics | grep -E "otelcol_receiver_accepted_spans|otelcol_exporter_send_failed_spans" \
  || echo "(no spans accepted yet — run the agent first)"

echo
echo "✅ Stack reachable. Dashboards: http://localhost:5601 ($OS_USER / $OS_PASS)"
