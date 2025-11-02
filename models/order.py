from datetime import UTC, datetime
from typing import Self

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import joinedload, relationship

from constants import DEFAULT_ORG_ID
from constants.order import OrderStatus, OrderType, UrgencyLevel
from db.postgres import Base, get_session

from .mixins import CRUDMixin, IDMixin


class Operator(Base, IDMixin, CRUDMixin):
    """Operator model."""

    __tablename__ = "operators"

    user_id = Column(UUID, nullable=False)
    surname = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    patronymic = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    additional = Column(Text, nullable=True)


class Company(Base, IDMixin, CRUDMixin):
    """Delivery time window."""

    __tablename__ = "company"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    additional = Column(Text, nullable=True)

    orders = relationship("Order", backref="company")


class Order(Base, IDMixin, CRUDMixin):
    """Order model."""

    __tablename__ = "orders"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(Enum(OrderType, name="order_type", native_enum=True), default=OrderType.VSD, nullable=False)

    company_id = Column(UUID, ForeignKey("company.id", ondelete="RESTRICT"), nullable=False, index=True)

    status = Column(
        Enum(OrderStatus, name="order_status", native_enum=True),
        default=OrderStatus.CREATED,
        nullable=False,
        index=True,
    )
    urgency_level = Column(
        Enum(UrgencyLevel, name="urgency_level", native_enum=True),
        default=UrgencyLevel.STANDARD,
        nullable=False,
    )
    additional = Column(Text, nullable=True)

    operator_id = Column(UUID, nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", backref="orders")
    operator = relationship("Operator", backref="orders")

    @classmethod
    def _get_dependency_field_options(cls) -> tuple:
        return (
            joinedload(cls.company),
            joinedload(cls.operator),
        )

    @classmethod
    async def get_by_status(
        cls, status: OrderStatus, page: int = 1, page_size: int = 20, current_org: str = DEFAULT_ORG_ID
    ) -> tuple[list[Self], int]:
        """Get orders by status."""

        async with get_session(current_org) as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.status == status)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().unique().all()

            # Count total number
            total_query = select(func.count(cls.id)).where(cls.status == status)
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return orders, total

    @classmethod
    async def get_by_operator(
        cls, operator_id: UUID, page: int = 1, page_size: int = 20, current_org: str = DEFAULT_ORG_ID
    ) -> tuple[list[Self], int]:
        """Get operator orders."""

        async with get_session(current_org) as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.operator_id == operator_id)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            orders = result.scalars().all()

            # Count total number
            total_query = select(func.count(cls.id)).where(cls.operator_id == operator_id)
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return orders, total

    @classmethod
    async def get_by_status_and_operator(
        cls,
        status: OrderStatus,
        operator_id: UUID,
        page: int = 1,
        page_size: int = 20,
        current_org: str = DEFAULT_ORG_ID,
    ) -> tuple[list[Self], int]:
        """Get operator orders in a status."""

        async with get_session(current_org) as session:
            orders_query = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .where(cls.operator_id == operator_id)
                .where(cls.status == status)
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            orders_result = await session.execute(orders_query)
            orders = orders_result.scalars().all()

            # Count total number
            total_query = select(func.count(cls.id)).where(cls.operator_id == operator_id).where(cls.status == status)
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return orders, total

    @classmethod
    async def get_all(
        cls, page: int = 1, page_size: int = 20, current_org: str = DEFAULT_ORG_ID
    ) -> tuple[list[Self], int]:
        async with get_session(current_org) as session:
            request = (
                select(cls)
                .options(*cls._get_dependency_field_options())
                .limit(page_size)
                .offset((page - 1) * page_size)
                .order_by(cls.created_at.desc())
            )
            result = await session.execute(request)
            entities = result.scalars().unique().all()

            # Count total number
            total_query = select(func.count(cls.id))
            total_result = await session.execute(total_query)
            total = total_result.scalar()

        return entities, total

    @classmethod
    async def get_by_id(cls, id_: UUID, current_org: str = DEFAULT_ORG_ID) -> Self:
        async with get_session(current_org) as session:
            request = select(cls).options(*cls._get_dependency_field_options()).where(cls.id == id_)
            result = await session.execute(request)
            return result.scalars().unique().first()

    async def assign_operator(self, operator_id: UUID, commit: bool = True, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Assign a operator to order."""

        self.operator_id = operator_id
        self.status = OrderStatus.ASSIGNED
        self.assigned_at = datetime.now(UTC)
        return await self.save(commit=commit, current_org=current_org)

    async def start_work(self, commit: bool = True, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Start work."""

        self.status = OrderStatus.IN_PROGRESS
        return await self.save(commit=commit, current_org=current_org)

    async def complete_work(
        self,
        commit: bool = True,
        current_org: str = DEFAULT_ORG_ID,
    ) -> bool:
        """Complete delivery."""

        self.status = OrderStatus.COMPLETED
        self.finished_at = datetime.now(UTC)
        return await self.save(commit=commit, current_org=current_org)

    async def cancel_order(self, commit: bool = True, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Cancel order."""

        self.status = OrderStatus.CANCELLED
        self.finished_at = datetime.now(UTC)
        return await self.save(commit=commit, current_org=current_org)

    def __repr__(self) -> str:
        return f"<Order {self.id}>"
