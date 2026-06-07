# Submission Checklist

## Does it need to be live?

| Task | Needs live deploy? |
|---|---|
| Screen recording | **No** — record against `localhost:8000` or a public URL |
| Postman collection | **No** — import and run locally |
| Git push | **No** |
| Automated tests | **No** |
| **Public deployment** | **Yes** — required for full submission per assignment |

The assignment also says: if you cannot deploy, a **well-documented local setup** is acceptable. This repo supports both.

## Completed in repo

- [x] All 5 APIs + health check
- [x] PostgreSQL schema with idempotency
- [x] 10,000 sample events
- [x] 8 automated tests
- [x] Postman collection (`postman_collection.json`)
- [x] README with architecture, API docs, tradeoffs
- [x] Docker + Render deploy config
- [x] Demo walkthrough script (`scripts/demo_walkthrough.sh`)

## You still need to do (manual)

### 1. Screen recording (~10 min)

Record using Loom / OBS / phone. Follow `scripts/demo_walkthrough.sh` or Postman.

**Suggested flow:**
1. Show README architecture (30 sec)
2. Start service (`docker compose up` or `uvicorn`)
3. Open `/docs` — show OpenAPI
4. `POST /events` — ingest + duplicate
5. `GET /transactions` — filters
6. `GET /transactions/{id}` — event history
7. `GET /reconciliation/summary`
8. `GET /reconciliation/discrepancies`

### 2. GitHub repo (~5 min)

```bash
cd pinelabs
git init
git add .
git commit -m "Add Setu partner reconciliation service"
gh auth login
gh repo create pinelabs-reconciliation --public --source=. --push
```

### 3. Deploy to Render (~15 min)

1. Push repo to GitHub
2. Go to [render.com](https://render.com) → New Blueprint → connect repo
3. Render reads `render.yaml` and creates Postgres + web service
4. After deploy, seed data:

```bash
python scripts/seed_events.py --api https://YOUR-APP.onrender.com
```

5. Add the URL to `README.md` under **Deployment URL**

### 4. Submit

Send to Pine Labs hiring team:
- GitHub repo link
- Live deployment URL (or note that local setup is documented)
- Postman collection (in repo)
- Screen recording link
