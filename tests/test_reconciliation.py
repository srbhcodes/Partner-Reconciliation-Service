from datetime import datetime, timezone


def _ingest(client, event_id, txn_id, event_type):
    payload = {
        "event_id": event_id,
        "event_type": event_type,
        "transaction_id": txn_id,
        "merchant_id": "merchant_3",
        "merchant_name": "TechZone",
        "amount": 5000.0,
        "currency": "INR",
        "timestamp": datetime(2026, 1, 12, 9, 0, 0, tzinfo=timezone.utc).isoformat(),
    }
    return client.post("/events", json=payload)


def test_reconciliation_summary(client):
    _ingest(client, "r1", "rt1", "payment_initiated")
    _ingest(client, "r2", "rt1", "payment_processed")
    _ingest(client, "r3", "rt1", "settled")

    response = client.get("/reconciliation/summary", params={"group_by": "merchant"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) >= 1


def test_discrepancy_processed_not_settled(client):
    _ingest(client, "d1", "dt1", "payment_initiated")
    _ingest(client, "d2", "dt1", "payment_processed")

    response = client.get("/reconciliation/discrepancies")
    assert response.status_code == 200
    body = response.json()
    types = {item["discrepancy_type"] for item in body["items"]}
    assert "processed_not_settled" in types


def test_discrepancy_settled_after_failure(client):
    _ingest(client, "f1", "ft1", "payment_initiated")
    _ingest(client, "f2", "ft1", "payment_failed")
    _ingest(client, "f3", "ft1", "settled")

    response = client.get("/reconciliation/discrepancies")
    body = response.json()
    types = {item["discrepancy_type"] for item in body["items"]}
    assert "settled_after_failure" in types
