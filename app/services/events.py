import json

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Event,
    EventType,
    Merchant,
    PaymentStatus,
    SettlementStatus,
    Transaction,
)
from app.schemas import EventCreate, EventResponse


EVENT_TYPE_MAP = {
    "payment_initiated": EventType.PAYMENT_INITIATED,
    "payment_processed": EventType.PAYMENT_PROCESSED,
    "payment_failed": EventType.PAYMENT_FAILED,
    "settled": EventType.SETTLED,
}


def _upsert_merchant(db: Session, merchant_id: str, merchant_name: str) -> Merchant:
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        merchant = Merchant(id=merchant_id, name=merchant_name)
        db.add(merchant)
    elif merchant.name != merchant_name:
        merchant.name = merchant_name
    return merchant


def _apply_event_to_transaction(
    transaction: Transaction, event_type: EventType, timestamp
) -> None:
    if event_type == EventType.PAYMENT_INITIATED:
        transaction.payment_status = PaymentStatus.INITIATED
        transaction.settlement_status = SettlementStatus.PENDING
        if transaction.initiated_at is None:
            transaction.initiated_at = timestamp

    elif event_type == EventType.PAYMENT_PROCESSED:
        if transaction.payment_status != PaymentStatus.FAILED:
            transaction.payment_status = PaymentStatus.PROCESSED
        if transaction.settlement_status == SettlementStatus.NOT_APPLICABLE:
            transaction.settlement_status = SettlementStatus.PENDING
        if transaction.processed_at is None:
            transaction.processed_at = timestamp

    elif event_type == EventType.PAYMENT_FAILED:
        transaction.payment_status = PaymentStatus.FAILED
        transaction.settlement_status = SettlementStatus.NOT_APPLICABLE
        if transaction.failed_at is None:
            transaction.failed_at = timestamp

    elif event_type == EventType.SETTLED:
        transaction.settlement_status = SettlementStatus.SETTLED
        if transaction.settled_at is None:
            transaction.settled_at = timestamp


def ingest_event(db: Session, payload: EventCreate) -> EventResponse:
    existing = (
        db.query(Event).filter(Event.event_id == payload.event_id).one_or_none()
    )
    if existing is not None:
        return EventResponse(
            event_id=existing.event_id,
            event_type=existing.event_type.value,
            transaction_id=existing.transaction_id,
            merchant_id=existing.merchant_id,
            amount=float(existing.amount),
            currency=existing.currency,
            timestamp=existing.timestamp,
            duplicate=True,
        )

    _upsert_merchant(db, payload.merchant_id, payload.merchant_name)

    transaction = db.get(Transaction, payload.transaction_id)
    if transaction is None:
        transaction = Transaction(
            id=payload.transaction_id,
            merchant_id=payload.merchant_id,
            amount=payload.amount,
            currency=payload.currency,
        )
        db.add(transaction)
    else:
        transaction.amount = payload.amount
        transaction.currency = payload.currency

    event_type = EVENT_TYPE_MAP[payload.event_type]
    event = Event(
        event_id=payload.event_id,
        event_type=event_type,
        transaction_id=payload.transaction_id,
        merchant_id=payload.merchant_id,
        amount=payload.amount,
        currency=payload.currency,
        timestamp=payload.timestamp,
        raw_payload=json.dumps(payload.model_dump(mode="json")),
    )

    try:
        db.add(event)
        _apply_event_to_transaction(transaction, event_type, payload.timestamp)
        db.commit()
        db.refresh(event)
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(Event).filter(Event.event_id == payload.event_id).one()
        )
        return EventResponse(
            event_id=existing.event_id,
            event_type=existing.event_type.value,
            transaction_id=existing.transaction_id,
            merchant_id=existing.merchant_id,
            amount=float(existing.amount),
            currency=existing.currency,
            timestamp=existing.timestamp,
            duplicate=True,
        )

    return EventResponse(
        event_id=event.event_id,
        event_type=event.event_type.value,
        transaction_id=event.transaction_id,
        merchant_id=event.merchant_id,
        amount=float(event.amount),
        currency=event.currency,
        timestamp=event.timestamp,
        duplicate=False,
    )
