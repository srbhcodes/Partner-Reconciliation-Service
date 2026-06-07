"""Load sample_events.json into the API or database directly."""

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT / "sample_events.json"


def seed_via_api(base_url: str, events: list[dict], batch_size: int = 100) -> None:
    created = duplicates = errors = 0
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for i, event in enumerate(events, start=1):
            response = client.post("/events", json=event)
            if response.status_code == 201:
                created += 1
            elif response.status_code == 200:
                duplicates += 1
            else:
                errors += 1
                print(f"Error on event {event['event_id']}: {response.text}", file=sys.stderr)

            if i % batch_size == 0:
                print(f"Processed {i}/{len(events)} events...")

    print(f"Done. created={created}, duplicates={duplicates}, errors={errors}")


def seed_via_db(events: list[dict]) -> None:
    sys.path.insert(0, str(ROOT))
    from app.database import SessionLocal
    from app.schemas import EventCreate
    from app.services.events import ingest_event

    db = SessionLocal()
    created = duplicates = 0
    try:
        for i, raw in enumerate(events, start=1):
            result = ingest_event(db, EventCreate(**raw))
            if result.duplicate:
                duplicates += 1
            else:
                created += 1
            if i % 500 == 0:
                print(f"Processed {i}/{len(events)} events...")
    finally:
        db.close()

    print(f"Done. created={created}, duplicates={duplicates}")


def main():
    parser = argparse.ArgumentParser(description="Seed payment events")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument("--api", type=str, default=None, help="Base URL e.g. http://localhost:8000")
    args = parser.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}. Run scripts/generate_sample_events.py first.")
        sys.exit(1)

    events = json.loads(args.file.read_text())
    print(f"Loading {len(events)} events from {args.file}")

    if args.api:
        seed_via_api(args.api.rstrip("/"), events)
    else:
        seed_via_db(events)


if __name__ == "__main__":
    main()
