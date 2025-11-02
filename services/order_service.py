import logging
from uuid import UUID

from fastapi import HTTPException

from constants import DEFAULT_ORG_ID
from constants.order import OrderStatus
from db.postgres import get_session
from models.order import Order
from schemas.order import (
    OrderCreate,
    OrderList,
    OrderResponse,
    OrderUpdate,
)

logger = logging.getLogger(__name__)


class OrderService:
    """Service for working with orders."""

    def __init__(self):
        """Initialize the OrderService."""

        self.model = Order

    async def create_order(self, order_data: OrderCreate, current_org: str = DEFAULT_ORG_ID) -> OrderResponse:
        """Create a new order."""

        async with get_session(current_org) as session:
            order_db = self.model(
                **order_data.model_dump(
                    exclude={"sender", "recipient", "package_details", "time_windows"}, exclude_none=True
                ),
                org_id=UUID(current_org),
            )
            session.add(order_db)
            await session.flush()

            await session.commit()
            await session.refresh(order_db)

            # Преобразуем в Pydantic модель
            return OrderResponse(
                id=order_db.id,
            )

    async def get_order_by_id(self, order_id: UUID, current_org: str = DEFAULT_ORG_ID) -> OrderResponse:
        """Get order by ID."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return OrderResponse.model_validate(order, from_attributes=True)

    async def get_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status: OrderStatus | None = None,
        operator_id: UUID | None = None,
        current_org: str = DEFAULT_ORG_ID,
    ) -> OrderList:
        """Get list of orders with filtering."""

        if status and operator_id:
            orders, total = await self.model.get_by_status_and_operator(
                status, operator_id, page, page_size, current_org=current_org
            )
        elif status:
            orders, total = await self.model.get_by_status(status, page, page_size, current_org=current_org)
        elif operator_id:
            orders, total = await self.model.get_by_operator(operator_id, page, page_size, current_org=current_org)
        else:
            orders, total = await self.model.get_all(page, page_size, current_org=current_org)

        order_responses = [OrderResponse.model_validate(order, from_attributes=True) for order in orders]

        return OrderList(orders=order_responses, total=total, page=page, page_size=page_size)

    async def update_order(
        self, order_id: UUID, order_data: OrderUpdate, current_org: str = DEFAULT_ORG_ID
    ) -> OrderResponse:
        """Update order."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Cannot edit delivered or cancelled order")

        # Update only provided fields
        update_data = order_data.model_dump(exclude_unset=True)
        order = await order.update(**update_data, current_org=current_org)

        return OrderResponse.model_validate(order, from_attributes=True)

    async def assign_courier(
        self, order_id: UUID, courier_id: UUID, current_org: str = DEFAULT_ORG_ID
    ) -> OrderResponse:
        """Assign a courier to order."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.CREATED:
            raise HTTPException(status_code=400, detail="Can only assign courier to order with 'created' status")

        order = await order.assign_operator(courier_id, current_org=current_org)
        return OrderResponse.model_validate(order, from_attributes=True)

    async def start_work(self, order_id: UUID, current_org: str = DEFAULT_ORG_ID) -> OrderResponse:
        """Start order work."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.ASSIGNED:
            raise HTTPException(status_code=400, detail="Can only start delivery for assigned order")

        await order.start_work(current_org=current_org)
        return OrderResponse.model_validate(order, from_attributes=True)

    async def complete_work(
        self,
        order_id: UUID,
        current_org: str = DEFAULT_ORG_ID,
    ) -> OrderResponse:
        """Complete order delivery."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status != OrderStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Can only complete order that is in progress")

        await order.complete_work(current_org=current_org)
        return OrderResponse.model_validate(order, from_attributes=True)

    async def cancel_order(self, order_id: UUID, current_org: str = DEFAULT_ORG_ID) -> OrderResponse:
        """Cancel order."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Cannot cancel delivered or already cancelled order")

        await order.cancel_order(current_org=current_org)
        return OrderResponse.model_validate(order, from_attributes=True)

    async def delete_order(self, order_id: UUID, current_org: str = DEFAULT_ORG_ID) -> bool:
        """Delete order."""

        order = await self.model.get_by_id(order_id, current_org=current_org)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.status not in [OrderStatus.CREATED, OrderStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Can only delete created or cancelled order")

        await order.delete(current_org=current_org)
        return True


order_service = OrderService()
