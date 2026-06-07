"""Generate sample_events.json with 10,000+ realistic payment lifecycle events."""

import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

MERCHANTS = [
    ("merchant_1", "QuickMart"),
    ("merchant_2", "FreshBasket"),
    ("merchant_3", "TechZone"),
    ("merchant_4", "StyleHub"),
    ("merchant_5", "TravelEase"),
]

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _ts(offset_minutes: int) -> str:
    return (BASE_TIME + timedelta(minutes=offset_minutes)).isoformat()


def _event(
    event_type: str,
    txn_id: str,
    merchant_id: str,
    merchant_name: str,
    amount: float,
    offset_minutes: int,
    event_id: str | None = None,
) -> dict:
    return {
        "event_id": event_id or str(uuid.uuid4()),
        "event_type": event_type,
        "transaction_id": txn_id,
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "amount": round(amount, 2),
        "currency": "INR",
        "timestamp": _ts(offset_minutes),
    }


def generate_events(target_count: int = 10000) -> list[dict]:
    events: list[dict] = []
    minute_cursor = 0

    # Successful flows (~60% of transactions)
    success_txns = int(target_count * 0.15)
    for i in range(success_txns):
        txn_id = str(uuid.uuid4())
        merchant_id, merchant_name = random.choice(MERCHANTS)
        amount = round(random.uniform(100, 50000), 2)
        initiated_id = str(uuid.uuid4())
        processed_id = str(uuid.uuid4())
        settled_id = str(uuid.uuid4())

        events.append(
            _event(
                "payment_initiated",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor,
                initiated_id,
            )
        )
        events.append(
            _event(
                "payment_processed",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor + 2,
                processed_id,
            )
        )
        events.append(
            _event(
                "settled",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor + 10,
                settled_id,
            )
        )
        minute_cursor += 1

    # Failed payments (~20%)
    failed_txns = int(target_count * 0.05)
    for _ in range(failed_txns):
        txn_id = str(uuid.uuid4())
        merchant_id, merchant_name = random.choice(MERCHANTS)
        amount = round(random.uniform(100, 30000), 2)
        events.append(
            _event(
                "payment_initiated",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor,
            )
        )
        events.append(
            _event(
                "payment_failed",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor + 3,
            )
        )
        minute_cursor += 1

    # Processed but never settled (~10% discrepancies)
    pending_txns = int(target_count * 0.025)
    for _ in range(pending_txns):
        txn_id = str(uuid.uuid4())
        merchant_id, merchant_name = random.choice(MERCHANTS)
        amount = round(random.uniform(500, 40000), 2)
        events.append(
            _event(
                "payment_initiated",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor,
            )
        )
        events.append(
            _event(
                "payment_processed",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor + 2,
            )
        )
        minute_cursor += 1

    # Settled after failure (~discrepancy)
    bad_settle = int(target_count * 0.005)
    for _ in range(bad_settle):
        txn_id = str(uuid.uuid4())
        merchant_id, merchant_name = random.choice(MERCHANTS)
        amount = round(random.uniform(1000, 20000), 2)
        events.append(
            _event(
                "payment_initiated",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor,
            )
        )
        events.append(
            _event(
                "payment_failed",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor + 2,
            )
        )
        events.append(
            _event(
                "settled",
                txn_id,
                merchant_id,
                merchant_name,
                amount,
                minute_cursor + 5,
            )
        )
        minute_cursor += 1

    # Duplicate events (~5% of events duplicated)
    duplicate_count = max(200, int(len(events) * 0.05))
    duplicates = random.sample(events, min(duplicate_count, len(events)))
    events.extend(duplicates)

    random.shuffle(events)

    # Pad to target if needed with more successful flows
    while len(events) < target_count:
        txn_id = str(uuid.uuid4())
        merchant_id, merchant_name = random.choice(MERCHANTS)
        amount = round(random.uniform(100, 25000), 2)
        events.extend(
            [
                _event(
                    "payment_initiated",
                    txn_id,
                    merchant_id,
                    merchant_name,
                    amount,
                    minute_cursor,
                ),
                _event(
                    "payment_processed",
                    txn_id,
                    merchant_id,
                    merchant_name,
                    amount,
                    minute_cursor + 1,
                ),
                _event(
                    "settled",
                    txn_id,
                    merchant_id,
                    merchant_name,
                    amount,
                    minute_cursor + 5,
                ),
            ]
        )
        minute_cursor += 1

    return events[: max(target_count, len(events))]


def main():
    output = Path(__file__).resolve().parent.parent / "sample_events.json"
    events = generate_events(10000)
    output.write_text(json.dumps(events, indent=2))
    print(f"Wrote {len(events)} events to {output}")


if __name__ == "__main__":
    main()
