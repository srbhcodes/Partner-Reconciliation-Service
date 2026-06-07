from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=64)
    event_type: Literal[
        "payment_initiated", "payment_processed", "payment_failed", "settled"
    ]
    transaction_id: str = Field(..., min_length=1, max_length=64)
    merchant_id: str = Field(..., min_length=1, max_length=64)
    merchant_name: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=8)
    timestamp: datetime


class EventResponse(BaseModel):
    event_id: str
    event_type: str
    transaction_id: str
    merchant_id: str
    amount: float
    currency: str
    timestamp: datetime
    duplicate: bool = False

    model_config = {"from_attributes": True}


class MerchantInfo(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class TransactionSummary(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str | None = None
    amount: float
    currency: str
    payment_status: str
    settlement_status: str
    initiated_at: datetime | None = None
    processed_at: datetime | None = None
    failed_at: datetime | None = None
    settled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionDetail(TransactionSummary):
    merchant: MerchantInfo
    events: list[EventResponse]


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class TransactionListResponse(BaseModel):
    items: list[TransactionSummary]
    pagination: PaginationMeta


class ReconciliationSummaryItem(BaseModel):
    group_key: str
    group_value: str
    transaction_count: int
    total_amount: float
    payment_status_breakdown: dict[str, int]
    settlement_status_breakdown: dict[str, int]


class ReconciliationSummaryResponse(BaseModel):
    group_by: str
    items: list[ReconciliationSummaryItem]
    filters: dict[str, str | None]


class DiscrepancyItem(BaseModel):
    transaction_id: str
    merchant_id: str
    merchant_name: str
    amount: float
    currency: str
    payment_status: str
    settlement_status: str
    discrepancy_type: str
    description: str


class DiscrepancyListResponse(BaseModel):
    items: list[DiscrepancyItem]
    total: int
