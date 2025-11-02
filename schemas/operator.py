from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .base import Model
from .mixins import IdMixin


class OperatorBase(BaseModel):
    user_id: UUID
    surname: str
    name: str
    patronymic: str | None = None
    description: str | None = None
    phone: str
    email: str | None = None
    additional: str | None = None


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    user_id: UUID | None = None
    surname: str | None = None
    name: str | None = None
    patronymic: str | None = None
    description: str | None = None
    phone: str | None = None
    email: str | None = None
    additional: str | None = None


class OperatorResponse(Model, IdMixin):
    user_id: UUID
    surname: str
    name: str
    patronymic: str | None = None
    description: str | None = None
    phone: str
    email: str | None = None
    additional: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
