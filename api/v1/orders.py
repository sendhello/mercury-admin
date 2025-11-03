from typing import Annotated
from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, Path, Query

from api.utils import PaginateQueryParams
from constants.order import OrderStatus
from schemas.order import OrderAssign, OrderCreate, OrderDeliveryComplete, OrderList, OrderResponse, OrderUpdate
from security import (
    DISPATCHER_REQUIRED,
    multitenancy_protected,
)
from services.order_service import order_service

router = APIRouter()


@router.post("/", response_model=OrderResponse, summary="Create order", dependencies=DISPATCHER_REQUIRED)
async def create_order(
    order_data: OrderCreate, auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected)
) -> OrderResponse:
    """Create a new order."""

    _, _, org_id = auth_data
    return await order_service.create_order(order_data, current_org=org_id)


@router.get("/", response_model=OrderList, summary="Get list of orders")
async def get_orders(
    paginate: Annotated[PaginateQueryParams, Depends(PaginateQueryParams)],
    status: OrderStatus = Query(None, description="Filter by status"),
    courier_id: UUID = Query(None, description="Filter by status"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderList:
    """Get list of orders with filtering options."""

    _, user_claims, org_id = auth_data
    return await order_service.get_orders(paginate.page, paginate.page_size, status, courier_id, current_org=org_id)


@router.get("/{order_id}", response_model=OrderResponse, summary="Get order by ID", dependencies=DISPATCHER_REQUIRED)
async def get_order_by_id(
    order_id: UUID = Path(description="ID of the order to retrieve"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderResponse:
    """Get order by ID."""

    _, user_claims, org_id = auth_data
    return await order_service.get_order_by_id(order_id, current_org=org_id)


@router.put("/{order_id}", response_model=OrderResponse, summary="Update order", dependencies=DISPATCHER_REQUIRED)
async def update_order(
    order_data: OrderUpdate,
    order_id: UUID = Path(description="ID of the order to update"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderResponse:
    """Update order data."""

    _, _, org_id = auth_data
    return await order_service.update_order(order_id, order_data, current_org=org_id)


@router.post(
    "/{order_id}/assign", response_model=OrderResponse, summary="Assign courier", dependencies=DISPATCHER_REQUIRED
)
async def assign_courier(
    assign_data: OrderAssign,
    order_id: UUID = Path(description="ID of the order to assign courier"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderResponse:
    """Assign courier to order."""

    _, user_claims, org_id = auth_data
    return await order_service.assign_courier(order_id, assign_data.courier_id, current_org=org_id)


@router.post(
    "/{order_id}/start", response_model=OrderResponse, summary="Start delivery", dependencies=DISPATCHER_REQUIRED
)
async def start_work(
    order_id: UUID = Path(description="ID of the order to start delivery"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderResponse:
    """Start order delivery."""

    _, user_claims, org_id = auth_data
    return await order_service.start_delivery(order_id, current_org=org_id)


@router.post(
    "/{order_id}/complete", response_model=OrderResponse, summary="Complete delivery", dependencies=DISPATCHER_REQUIRED
)
async def complete_delivery(
    completion_data: OrderDeliveryComplete,
    order_id: UUID = Path(description="ID of the order to complete delivery"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderResponse:
    """Complete order delivery."""

    _, user_claims, org_id = auth_data
    return await order_service.complete_delivery(
        order_id, completion_data.delivery_photo_url, completion_data.recipient_signature, current_org=org_id
    )


@router.post(
    "/{order_id}/cancel", response_model=OrderResponse, summary="Cancel order", dependencies=DISPATCHER_REQUIRED
)
async def cancel_order(
    order_id: UUID = Path(description="ID of the order to cancel"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OrderResponse:
    """Cancel order."""

    _, user_claims, org_id = auth_data
    return await order_service.cancel_order(order_id, current_org=org_id)


@router.delete("/{order_id}", summary="Delete order", dependencies=DISPATCHER_REQUIRED)
async def delete_order(
    order_id: UUID = Path(description="ID of the order to delete"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> dict:
    """Delete order."""

    _, user_claims, org_id = auth_data
    await order_service.delete_order(order_id, current_org=org_id)
    return {"message": "Order successfully deleted"}
