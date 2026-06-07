import math
from datetime import datetime

from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models import Merchant, PaymentStatus, SettlementStatus, Transaction
from app.schemas import (
    EventResponse,
    MerchantInfo,
    PaginationMeta,
    TransactionDetail,
    TransactionListResponse,
    TransactionSummary,
)

SORTABLE_FIELDS = {
    "created_at": Transaction.created_at,
    "updated_at": Transaction.updated_at,
    "amount": Transaction.amount,
    "initiated_at": Transaction.initiated_at,
}


def _to_summary(txn: Transaction) -> TransactionSummary:
    return TransactionSummary(
        id=txn.id,
        merchant_id=txn.merchant_id,
        merchant_name=txn.merchant.name if txn.merchant else None,
        amount=float(txn.amount),
        currency=txn.currency,
        payment_status=txn.payment_status.value,
        settlement_status=txn.settlement_status.value,
        initiated_at=txn.initiated_at,
        processed_at=txn.processed_at,
        failed_at=txn.failed_at,
        settled_at=txn.settled_at,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
    )


def list_transactions(
    db: Session,
    *,
    merchant_id: str | None = None,
    status: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> TransactionListResponse:
    query = db.query(Transaction).join(Merchant)

    if merchant_id:
        query = query.filter(Transaction.merchant_id == merchant_id)

    if status:
        try:
            payment_status = PaymentStatus(status)
            query = query.filter(Transaction.payment_status == payment_status)
        except ValueError:
            try:
                settlement_status = SettlementStatus(status)
                query = query.filter(Transaction.settlement_status == settlement_status)
            except ValueError:
                pass

    if from_date:
        query = query.filter(Transaction.created_at >= from_date)
    if to_date:
        query = query.filter(Transaction.created_at <= to_date)

    total_items = query.with_entities(func.count(Transaction.id)).scalar() or 0
    total_pages = max(1, math.ceil(total_items / page_size)) if total_items else 0

    sort_column = SORTABLE_FIELDS.get(sort_by, Transaction.created_at)
    order_fn = desc if sort_order.lower() == "desc" else asc

    transactions = (
        query.options(joinedload(Transaction.merchant))
        .order_by(order_fn(sort_column))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return TransactionListResponse(
        items=[_to_summary(txn) for txn in transactions],
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
        ),
    )


def get_transaction_detail(db: Session, transaction_id: str) -> TransactionDetail | None:
    txn = (
        db.query(Transaction)
        .options(joinedload(Transaction.merchant), joinedload(Transaction.events))
        .filter(Transaction.id == transaction_id)
        .one_or_none()
    )
    if txn is None:
        return None

    return TransactionDetail(
        id=txn.id,
        merchant_id=txn.merchant_id,
        merchant_name=txn.merchant.name,
        amount=float(txn.amount),
        currency=txn.currency,
        payment_status=txn.payment_status.value,
        settlement_status=txn.settlement_status.value,
        initiated_at=txn.initiated_at,
        processed_at=txn.processed_at,
        failed_at=txn.failed_at,
        settled_at=txn.settled_at,
        created_at=txn.created_at,
        updated_at=txn.updated_at,
        merchant=MerchantInfo(id=txn.merchant.id, name=txn.merchant.name),
        events=[
            EventResponse(
                event_id=e.event_id,
                event_type=e.event_type.value,
                transaction_id=e.transaction_id,
                merchant_id=e.merchant_id,
                amount=float(e.amount),
                currency=e.currency,
                timestamp=e.timestamp,
                duplicate=False,
            )
            for e in txn.events
        ],
    )
