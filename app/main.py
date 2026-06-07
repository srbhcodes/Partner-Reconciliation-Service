from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import events, reconciliation, transactions


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Setu Partner Reconciliation Service",
    description="Payment event ingestion, transaction APIs, and reconciliation reporting.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(events.router)
app.include_router(transactions.router)
app.include_router(reconciliation.router)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
