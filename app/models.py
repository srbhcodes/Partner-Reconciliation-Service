import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentStatus(str, enum.Enum):
    INITIATED = "initiated"
    PROCESSED = "processed"
    FAILED = "failed"


class SettlementStatus(str, enum.Enum):
    PENDING = "pending"
    SETTLED = "settled"
    NOT_APPLICABLE = "not_applicable"


class EventType(str, enum.Enum):
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_PROCESSED = "payment_processed"
    PAYMENT_FAILED = "payment_failed"
    SETTLED = "settled"


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="merchant")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_merchant_id", "merchant_id"),
        Index("ix_transactions_payment_status", "payment_status"),
        Index("ix_transactions_settlement_status", "settlement_status"),
        Index("ix_transactions_created_at", "created_at"),
        Index("ix_transactions_merchant_status", "merchant_id", "payment_status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("merchants.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="INR")
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status_enum", native_enum=False),
        nullable=False,
        default=PaymentStatus.INITIATED,
    )
    settlement_status: Mapped[SettlementStatus] = mapped_column(
        Enum(SettlementStatus, name="settlement_status_enum", native_enum=False),
        nullable=False,
        default=SettlementStatus.PENDING,
    )
    initiated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="transactions")
    events: Mapped[list["Event"]] = relationship(
        back_populates="transaction", order_by="Event.timestamp"
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_events_event_id"),
        Index("ix_events_transaction_id", "transaction_id"),
        Index("ix_events_timestamp", "timestamp"),
        Index("ix_events_merchant_id", "merchant_id"),
        Index("ix_events_event_type", "event_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type_enum", native_enum=False), nullable=False
    )
    transaction_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("transactions.id"), nullable=False
    )
    merchant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("merchants.id"), nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    raw_payload: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    transaction: Mapped["Transaction"] = relationship(back_populates="events")
