from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DiscrepancyListResponse, ReconciliationSummaryResponse
from app.services.reconciliation import get_discrepancies, get_reconciliation_summary

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


@router.get(
    "/summary",
    response_model=ReconciliationSummaryResponse,
    summary="Reconciliation summary grouped by merchant, date, or status",
)
def reconciliation_summary(
    group_by: str = Query(
        default="merchant",
        pattern="^(merchant|date|status)$",
        description="Group results by merchant, date, or status",
    ),
    merchant_id: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> ReconciliationSummaryResponse:
    return get_reconciliation_summary(
        db,
        group_by=group_by,
        merchant_id=merchant_id,
        from_date=from_date,
        to_date=to_date,
    )


@router.get(
    "/discrepancies",
    response_model=DiscrepancyListResponse,
    summary="List transactions with payment/settlement inconsistencies",
)
def reconciliation_discrepancies(
    merchant_id: str | None = Query(default=None),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DiscrepancyListResponse:
    return get_discrepancies(
        db,
        merchant_id=merchant_id,
        from_date=from_date,
        to_date=to_date,
    )
