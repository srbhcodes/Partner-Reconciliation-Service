# Setu Partner Reconciliation Service

Backend service for ingesting payment lifecycle events, maintaining transaction state, and exposing reconciliation APIs for operations teams.

Built for the Pine Labs Solutions Engineer take-home assignment.

## Architecture Overview

```
Client / Partner Systems
        |
        v
   FastAPI (REST)
        |
        v
   Service Layer (events, transactions, reconciliation)
        |
        v
   PostgreSQL (merchants, transactions, events)
```

### Components

- **FastAPI** — REST API with OpenAPI docs at `/docs`
- **PostgreSQL** — persistent storage with indexes for filter/sort queries
- **SQLAlchemy** — ORM and SQL aggregations for reconciliation

### Data Model

| Table | Purpose |
|---|---|
| `merchants` | Merchant identity (`id`, `name`) |
| `transactions` | Current payment + settlement state per transaction |
| `events` | Immutable event history; `event_id` is unique for idempotency |

### Idempotency

- `events.event_id` has a **unique constraint**
- Duplicate `POST /events` with the same `event_id` returns `200` with `duplicate: true`
- Transaction state is **not** updated on duplicate submissions
- Full event history is preserved (no overwrites)

### Reconciliation Rules

| Discrepancy Type | Condition |
|---|---|
| `processed_not_settled` | Payment processed, settlement still pending |
| `settled_after_failure` | Settlement recorded after payment failed |
| `failed_with_pending_settlement` | Failed payment with pending settlement |
| `settled_without_processing` | Settled before payment was processed |

## API Documentation

Interactive docs: `GET /docs`

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/events` | Ingest payment lifecycle event (idempotent) |
| `GET` | `/transactions` | List transactions with filters, pagination, sorting |
| `GET` | `/transactions/{id}` | Transaction detail + event history |
| `GET` | `/reconciliation/summary` | Aggregated summary by merchant, date, or status |
| `GET` | `/reconciliation/discrepancies` | Inconsistent payment/settlement states |
| `GET` | `/health` | Health check |

### Sample Event

```json
{
  "event_id": "b768e3a7-9eb3-4603-b21c-a54cc95661bc",
  "event_type": "payment_initiated",
  "transaction_id": "2f86e94c-239c-4302-9874-75f28e3474ee",
  "merchant_id": "merchant_2",
  "merchant_name": "FreshBasket",
  "amount": 15248.29,
  "currency": "INR",
  "timestamp": "2026-01-08T12:11:58.085567+00:00"
}
```

### Query Parameters

**`GET /transactions`**
- `merchant_id`, `status` (payment or settlement status)
- `from_date`, `to_date` (ISO 8601)
- `page`, `page_size` (max 100)
- `sort_by`: `created_at`, `updated_at`, `amount`, `initiated_at`
- `sort_order`: `asc` or `desc`

**`GET /reconciliation/summary`**
- `group_by`: `merchant` (default), `date`, or `status`
- `merchant_id`, `from_date`, `to_date`

## Sample Data

`sample_events.json` contains 10,000+ events across 5 merchants:

- Successful payment flows (initiated → processed → settled)
- Failed payments
- Processed-but-not-settled (discrepancies)
- Settled-after-failure (discrepancies)
- Duplicate events (~5%)

Generate fresh data:

```bash
python scripts/generate_sample_events.py
```

## Local Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (recommended)

### Option A: Docker Compose (fastest)

```bash
docker compose up --build
```

API: http://localhost:8000  
Docs: http://localhost:8000/docs

Seed data:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_sample_events.py
python scripts/seed_events.py --api http://localhost:8000
```

### Option B: Local Python + Postgres

```bash
cp .env.example .env
# Start Postgres locally, then:
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Seed directly to DB:

```bash
python scripts/seed_events.py
```

### Run Tests

```bash
pytest -v
```

### Postman

Import `postman_collection.json`. Set `baseUrl` to your deployment or `http://localhost:8000`.

## Deployment

### Render (recommended)

1. Push repo to GitHub
2. Create a new **Blueprint** from `render.yaml`
3. Render provisions a free PostgreSQL instance and web service
4. After deploy, seed via API:

```bash
python scripts/seed_events.py --api https://your-app.onrender.com
```

### Other Platforms

Works on Railway, Fly.io, AWS, GCP. Set `DATABASE_URL` and run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Deployment URL:** _Not deployed yet — see [SUBMISSION.md](./SUBMISSION.md) for deploy steps_

**Screen recording:** _Record locally with `./scripts/demo_walkthrough.sh` — live URL not required for the demo video_

## Assumptions & Tradeoffs

| Decision | Rationale |
|---|---|
| FastAPI over Flask | Built-in validation, OpenAPI docs, modern async support |
| Denormalized transaction state | Fast list/filter queries; events table preserves full history |
| `create_all` on startup | Simple for take-home; production would use Alembic migrations |
| Status filter accepts payment or settlement | Flexible ops filtering; documented in API |
| Duplicate events return 200 | Idempotent ingest without error noise |
| SQL aggregations for reconciliation | Meets requirement to avoid Python-side loops over large datasets |

### With More Time

- Alembic migrations instead of `create_all`
- Keyset pagination for very large datasets
- Background job for async event ingestion at scale
- Auth/API keys for partner endpoints
- Metrics and structured logging (OpenTelemetry)

## AI Tool Disclosure

Cursor AI was used to scaffold the project structure, generate sample data scripts, write tests, and draft documentation. All design decisions were reviewed and the code was validated with automated tests.

## Project Structure

```
app/
  main.py              # FastAPI app
  models.py            # SQLAlchemy models
  schemas.py           # Pydantic request/response models
  routers/             # API route handlers
  services/            # Business logic
scripts/
  generate_sample_events.py
  seed_events.py
tests/
postman_collection.json
docker-compose.yml
render.yaml
```
