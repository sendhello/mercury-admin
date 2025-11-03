from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from constants.order import OrderStatus, OrderType, UrgencyLevel

from .base import Model
from .mixins import IdMixin


class OrderBase(BaseModel):
    title: str
    description: str | None = None
    type: OrderType = OrderType.VSD
    company_id: UUID
    urgency_level: UrgencyLevel = UrgencyLevel.STANDARD
    additional: str | None = None


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    type: OrderType | None = None
    company_id: UUID | None = None
    status: OrderStatus | None = None
    urgency_level: UrgencyLevel | None = None
    additional: str | None = None
    operator_id: UUID | None = None


class OrderAssign(BaseModel):
    operator_id: UUID


class OrderDeliveryComplete(BaseModel):
    # Kept for API compatibility though current model doesn't store these fields
    delivery_photo_url: str | None = None
    recipient_signature: str | None = None


class OrderResponse(Model, IdMixin):
    title: str
    description: str | None = None
    type: OrderType
    company_id: UUID
    status: OrderStatus
    urgency_level: UrgencyLevel
    additional: str | None = None

    operator_id: UUID | None = None
    assigned_at: datetime | None = None
    finished_at: datetime | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None


class OrderList(Model):
    orders: list[OrderResponse]
    total: int
    page: int
    page_size: int
