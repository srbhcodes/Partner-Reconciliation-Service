#!/usr/bin/env bash
# Quick end-to-end API walkthrough for screen recording or smoke testing.
# Usage: ./scripts/demo_walkthrough.sh [base_url]
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
TXN_ID="demo-$(date +%s)"

echo "=== 1. Health check ==="
curl -s "$BASE_URL/health" | python3 -m json.tool

echo ""
echo "=== 2. Ingest payment_initiated ==="
curl -s -X POST "$BASE_URL/events" -H "Content-Type: application/json" -d "{
  \"event_id\": \"evt-init-$TXN_ID\",
  \"event_type\": \"payment_initiated\",
  \"transaction_id\": \"$TXN_ID\",
  \"merchant_id\": \"merchant_2\",
  \"merchant_name\": \"FreshBasket\",
  \"amount\": 15248.29,
  \"currency\": \"INR\",
  \"timestamp\": \"2026-01-08T12:11:58.085567+00:00\"
}" | python3 -m json.tool

echo ""
echo "=== 3. Ingest payment_processed ==="
curl -s -X POST "$BASE_URL/events" -H "Content-Type: application/json" -d "{
  \"event_id\": \"evt-proc-$TXN_ID\",
  \"event_type\": \"payment_processed\",
  \"transaction_id\": \"$TXN_ID\",
  \"merchant_id\": \"merchant_2\",
  \"merchant_name\": \"FreshBasket\",
  \"amount\": 15248.29,
  \"currency\": \"INR\",
  \"timestamp\": \"2026-01-08T12:12:10.085567+00:00\"
}" | python3 -m json.tool

echo ""
echo "=== 4. Duplicate event (idempotency) ==="
DUP_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST "$BASE_URL/events" -H "Content-Type: application/json" -d "{
  \"event_id\": \"evt-init-$TXN_ID\",
  \"event_type\": \"payment_initiated\",
  \"transaction_id\": \"$TXN_ID\",
  \"merchant_id\": \"merchant_2\",
  \"merchant_name\": \"FreshBasket\",
  \"amount\": 15248.29,
  \"currency\": \"INR\",
  \"timestamp\": \"2026-01-08T12:11:58.085567+00:00\"
}")
DUP_BODY="${DUP_RESPONSE%HTTPSTATUS:*}"
DUP_CODE="${DUP_RESPONSE##*HTTPSTATUS:}"
echo "$DUP_BODY" | python3 -m json.tool
echo "HTTP $DUP_CODE (expect 200 for duplicate)"

echo ""
echo "=== 5. List transactions ==="
curl -s "$BASE_URL/transactions?merchant_id=merchant_2&page=1&page_size=5" | python3 -m json.tool

echo ""
echo "=== 6. Transaction detail ==="
curl -s "$BASE_URL/transactions/$TXN_ID" | python3 -m json.tool

echo ""
echo "=== 7. Reconciliation summary ==="
curl -s "$BASE_URL/reconciliation/summary?group_by=merchant" | python3 -m json.tool

echo ""
echo "=== 8. Reconciliation discrepancies ==="
curl -s "$BASE_URL/reconciliation/discrepancies" | python3 -m json.tool

echo ""
echo "Done. OpenAPI docs: $BASE_URL/docs"
