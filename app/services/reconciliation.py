from datetime import datetime

from sqlalchemy import case, func, literal, or_, select
from sqlalchemy.orm import Session

from app.models import Merchant, PaymentStatus, SettlementStatus, Transaction
from app.schemas import (
    DiscrepancyItem,
    DiscrepancyListResponse,
    ReconciliationSummaryItem,
    ReconciliationSummaryResponse,
)


def get_reconciliation_summary(
    db: Session,
    *,
    group_by: str = "merchant",
    merchant_id: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> ReconciliationSummaryResponse:
    base = select(Transaction).join(Merchant)

    if merchant_id:
        base = base.where(Transaction.merchant_id == merchant_id)
    if from_date:
        base = base.where(Transaction.created_at >= from_date)
    if to_date:
        base = base.where(Transaction.created_at <= to_date)

    if group_by == "date":
        group_expr = func.date(Transaction.created_at)
        group_label = "date"
    elif group_by == "status":
        group_expr = Transaction.payment_status
        group_label = "payment_status"
    else:
        group_expr = Transaction.merchant_id
        group_label = "merchant_id"

    stmt = (
        select(
            group_expr.label("group_value"),
            func.count(Transaction.id).label("transaction_count"),
            func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
            func.count(case((Transaction.payment_status == PaymentStatus.INITIATED, 1))).label(
                "initiated_count"
            ),
            func.count(case((Transaction.payment_status == PaymentStatus.PROCESSED, 1))).label(
                "processed_count"
            ),
            func.count(case((Transaction.payment_status == PaymentStatus.FAILED, 1))).label(
                "failed_count"
            ),
            func.count(
                case((Transaction.settlement_status == SettlementStatus.PENDING, 1))
            ).label("pending_settlement_count"),
            func.count(
                case((Transaction.settlement_status == SettlementStatus.SETTLED, 1))
            ).label("settled_count"),
            func.count(
                case((Transaction.settlement_status == SettlementStatus.NOT_APPLICABLE, 1))
            ).label("not_applicable_count"),
        )
        .select_from(Transaction)
        .join(Merchant)
    )

    if merchant_id:
        stmt = stmt.where(Transaction.merchant_id == merchant_id)
    if from_date:
        stmt = stmt.where(Transaction.created_at >= from_date)
    if to_date:
        stmt = stmt.where(Transaction.created_at <= to_date)

    stmt = stmt.group_by(group_expr).order_by(group_expr)

    rows = db.execute(stmt).all()
    items = [
        ReconciliationSummaryItem(
            group_key=group_label,
            group_value=str(row.group_value),
            transaction_count=row.transaction_count,
            total_amount=float(row.total_amount),
            payment_status_breakdown={
                "initiated": row.initiated_count,
                "processed": row.processed_count,
                "failed": row.failed_count,
            },
            settlement_status_breakdown={
                "pending": row.pending_settlement_count,
                "settled": row.settled_count,
                "not_applicable": row.not_applicable_count,
            },
        )
        for row in rows
    ]

    return ReconciliationSummaryResponse(
        group_by=group_by,
        items=items,
        filters={
            "merchant_id": merchant_id,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
        },
    )


def _discrepancy_type(txn: Transaction) -> tuple[str, str] | None:
    if (
        txn.payment_status == PaymentStatus.PROCESSED
        and txn.settlement_status == SettlementStatus.PENDING
    ):
        return (
            "processed_not_settled",
            "Payment marked processed but settlement is still pending.",
        )

    if (
        txn.payment_status == PaymentStatus.FAILED
        and txn.settlement_status == SettlementStatus.SETTLED
    ):
        return (
            "settled_after_failure",
            "Settlement recorded for a failed payment.",
        )

    if (
        txn.payment_status == PaymentStatus.FAILED
        and txn.settlement_status == SettlementStatus.PENDING
    ):
        return (
            "failed_with_pending_settlement",
            "Failed payment still has pending settlement status.",
        )

    if (
        txn.payment_status == PaymentStatus.INITIATED
        and txn.settlement_status == SettlementStatus.SETTLED
    ):
        return (
            "settled_without_processing",
            "Settlement recorded before payment was processed.",
        )

    return None


def get_discrepancies(
    db: Session,
    *,
    merchant_id: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> DiscrepancyListResponse:
    query = db.query(Transaction).join(Merchant)

    if merchant_id:
        query = query.filter(Transaction.merchant_id == merchant_id)
    if from_date:
        query = query.filter(Transaction.created_at >= from_date)
    if to_date:
        query = query.filter(Transaction.created_at <= to_date)

    query = query.filter(
        or_(
            (Transaction.payment_status == PaymentStatus.PROCESSED)
            & (Transaction.settlement_status == SettlementStatus.PENDING),
            (Transaction.payment_status == PaymentStatus.FAILED)
            & (Transaction.settlement_status == SettlementStatus.SETTLED),
            (Transaction.payment_status == PaymentStatus.FAILED)
            & (Transaction.settlement_status == SettlementStatus.PENDING),
            (Transaction.payment_status == PaymentStatus.INITIATED)
            & (Transaction.settlement_status == SettlementStatus.SETTLED),
        )
    )

    transactions = query.order_by(Transaction.created_at.desc()).all()

    items: list[DiscrepancyItem] = []
    for txn in transactions:
        result = _discrepancy_type(txn)
        if result is None:
            continue
        discrepancy_type, description = result
        items.append(
            DiscrepancyItem(
                transaction_id=txn.id,
                merchant_id=txn.merchant_id,
                merchant_name=txn.merchant.name,
                amount=float(txn.amount),
                currency=txn.currency,
                payment_status=txn.payment_status.value,
                settlement_status=txn.settlement_status.value,
                discrepancy_type=discrepancy_type,
                description=description,
            )
        )

    return DiscrepancyListResponse(items=items, total=len(items))
