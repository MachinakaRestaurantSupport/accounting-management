"""Pydantic models for accounting-management."""

from typing import Literal

from pydantic import BaseModel, Field

PaymentMethod = Literal["cash", "card", "qr"]


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    service: str


class PaymentCreate(BaseModel):
    """Request payload for creating a payment."""

    order_id: str = Field(min_length=1)
    method: PaymentMethod
    received_amount: int = Field(ge=0)


class Payment(BaseModel):
    """Persisted payment and receipt record."""

    id: str
    order_id: str
    amount: int
    received_amount: int
    change_amount: int
    method: PaymentMethod
    receipt_number: str
    paid_at: str
