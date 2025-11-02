from datetime import datetime

from pydantic import BaseModel

from .base import Model
from .mixins import IdMixin


class CompanyBase(BaseModel):
    title: str
    description: str | None = None
    address: str
    phone: str
    email: str | None = None
    additional: str | None = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    additional: str | None = None


class CompanyResponse(Model, IdMixin):
    title: str
    description: str | None = None
    address: str
    phone: str
    email: str | None = None
    additional: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
