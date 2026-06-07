from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import TransactionDetail, TransactionListResponse
from app.services.transactions import get_transaction_detail, list_transactions

router = APIRouter(tags=["transactions"])


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="List transactions with filtering and pagination",
)
def get_transactions(
    merchant_id: str | None = Query(default=None),
    status: str | None = Query(
        default=None,
        description="Filter by payment_status or settlement_status value",
    ),
    from_date: datetime | None = Query(default=None),
    to_date: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(
        default="created_at",
        description="created_at, updated_at, amount, initiated_at",
    ),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    return list_transactions(
        db,
        merchant_id=merchant_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionDetail,
    summary="Fetch transaction details with event history",
)
def get_transaction(
    transaction_id: str, db: Session = Depends(get_db)
) -> TransactionDetail:
    detail = get_transaction_detail(db, transaction_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return detail
