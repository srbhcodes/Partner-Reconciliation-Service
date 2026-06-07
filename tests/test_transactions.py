from datetime import datetime, timezone


def _ingest(client, event_id, txn_id, event_type):
    payload = {
        "event_id": event_id,
        "event_type": event_type,
        "transaction_id": txn_id,
        "merchant_id": "merchant_2",
        "merchant_name": "FreshBasket",
        "amount": 2000.0,
        "currency": "INR",
        "timestamp": datetime(2026, 1, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
    }
    return client.post("/events", json=payload)


def test_list_transactions_with_filters(client):
    _ingest(client, "e1", "t1", "payment_initiated")
    _ingest(client, "e2", "t1", "payment_processed")
    _ingest(client, "e3", "t2", "payment_initiated")

    response = client.get("/transactions", params={"merchant_id": "merchant_2"})
    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total_items"] == 2


def test_transaction_detail_not_found(client):
    response = client.get("/transactions/missing-id")
    assert response.status_code == 404
