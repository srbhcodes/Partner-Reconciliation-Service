"""Load sample_events.json into the API or database directly."""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT / "sample_events.json"


def _post_event(base_url: str, event: dict) -> str:
    with httpx.Client(base_url=base_url, timeout=60.0) as client:
        response = client.post("/events", json=event)
        if response.status_code == 201:
            return "created"
        if response.status_code == 200:
            return "duplicate"
        raise RuntimeError(
            f"Error on event {event['event_id']}: {response.status_code} {response.text}"
        )


def seed_via_api(
    base_url: str, events: list[dict], batch_size: int = 100, concurrency: int = 8
) -> None:
    created = duplicates = errors = 0
    total = len(events)

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(_post_event, base_url, event): i
            for i, event in enumerate(events, start=1)
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
                if result == "created":
                    created += 1
                else:
                    duplicates += 1
            except Exception as exc:
                errors += 1
                print(str(exc), file=sys.stderr, flush=True)

            done = created + duplicates + errors
            if done % batch_size == 0 or done == total:
                print(
                    f"Processed {done}/{total} events "
                    f"(created={created}, duplicates={duplicates}, errors={errors})",
                    flush=True,
                )

    print(f"Done. created={created}, duplicates={duplicates}, errors={errors}", flush=True)


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
                print(f"Processed {i}/{len(events)} events...", flush=True)
    finally:
        db.close()

    print(f"Done. created={created}, duplicates={duplicates}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Seed payment events")
    parser.add_argument("--file", type=Path, default=DEFAULT_FILE)
    parser.add_argument(
        "--api", type=str, default=None, help="Base URL e.g. http://localhost:8000"
    )
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()

    if not args.file.exists():
        print(f"File not found: {args.file}. Run scripts/generate_sample_events.py first.")
        sys.exit(1)

    events = json.loads(args.file.read_text())
    print(f"Loading {len(events)} events from {args.file}", flush=True)

    if args.api:
        seed_via_api(args.api.rstrip("/"), events, concurrency=args.concurrency)
    else:
        seed_via_db(events)


if __name__ == "__main__":
    main()
