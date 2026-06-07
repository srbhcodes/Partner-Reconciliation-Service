from datetime import datetime, timezone


def _sample_event(event_id: str = "evt-1", transaction_id: str = "txn-1"):
    return {
        "event_id": event_id,
        "event_type": "payment_initiated",
        "transaction_id": transaction_id,
        "merchant_id": "merchant_1",
        "merchant_name": "QuickMart",
        "amount": 1500.50,
        "currency": "INR",
        "timestamp": datetime(2026, 1, 8, 12, 0, 0, tzinfo=timezone.utc).isoformat(),
    }


def test_ingest_event_creates_transaction(client):
    response = client.post("/events", json=_sample_event())
    assert response.status_code == 201
    body = response.json()
    assert body["duplicate"] is False
    assert body["event_id"] == "evt-1"


def test_duplicate_event_is_idempotent(client):
    first = client.post("/events", json=_sample_event())
    second = client.post("/events", json=_sample_event())

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["duplicate"] is True

    detail = client.get("/transactions/txn-1")
    assert detail.status_code == 200
    assert len(detail.json()["events"]) == 1


def test_full_payment_lifecycle(client):
    txn_id = "txn-lifecycle"
    base = _sample_event("evt-init", txn_id)
    client.post("/events", json=base)

    processed = {**base, "event_id": "evt-proc", "event_type": "payment_processed"}
    client.post("/events", json=processed)

    settled = {**base, "event_id": "evt-settle", "event_type": "settled"}
    client.post("/events", json=settled)

    detail = client.get(f"/transactions/{txn_id}")
    body = detail.json()
    assert body["payment_status"] == "processed"
    assert body["settlement_status"] == "settled"
    assert len(body["events"]) == 3
