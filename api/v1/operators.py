from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select

from db.postgres import get_session
from models import Operator
from schemas import OperatorCreate, OperatorResponse, OperatorUpdate
from security import DISPATCHER_REQUIRED, multitenancy_protected

router = APIRouter()


@router.post("/", response_model=OperatorResponse, summary="Create operator", dependencies=DISPATCHER_REQUIRED)
async def create_operator(
    operator_data: OperatorCreate,
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OperatorResponse:
    _, _, org_id = auth_data
    async with get_session(org_id) as session:
        operator = Operator(**operator_data.model_dump(exclude_none=True))
        session.add(operator)
        await session.flush()
        await session.commit()
        await session.refresh(operator)
    return OperatorResponse.model_validate(operator, from_attributes=True)


@router.get(
    "/",
    response_model=list[OperatorResponse],
    summary="List operators",
)
async def list_operators(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> list[OperatorResponse]:
    _, _, org_id = auth_data
    async with get_session(org_id) as session:
        result = await session.execute(select(Operator))
        operators = result.scalars().all()
    return [OperatorResponse.model_validate(i, from_attributes=True) for i in operators]


@router.get(
    "/{operator_id}",
    response_model=OperatorResponse,
    summary="Get operator by ID",
    dependencies=DISPATCHER_REQUIRED,
)
async def get_operator_by_id(
    operator_id: UUID = Path(description="ID of the operator to retrieve"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OperatorResponse:
    _, _, org_id = auth_data
    operator = await Operator.get_by_id(operator_id, current_org=org_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    return OperatorResponse.model_validate(operator, from_attributes=True)


@router.put(
    "/{operator_id}",
    response_model=OperatorResponse,
    summary="Update operator",
    dependencies=DISPATCHER_REQUIRED,
)
async def update_operator(
    operator_data: OperatorUpdate,
    operator_id: UUID = Path(description="ID of the operator to update"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> OperatorResponse:
    _, _, org_id = auth_data
    operator = await Operator.get_by_id(operator_id, current_org=org_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    update_data = operator_data.model_dump(exclude_unset=True)
    operator = await operator.update(current_org=org_id, **update_data)
    return OperatorResponse.model_validate(operator, from_attributes=True)


@router.delete(
    "/{operator_id}",
    summary="Delete operator",
    dependencies=DISPATCHER_REQUIRED,
)
async def delete_operator(
    operator_id: UUID = Path(description="ID of the operator to delete"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> dict:
    _, _, org_id = auth_data
    operator = await Operator.get_by_id(operator_id, current_org=org_id)
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    await operator.delete(current_org=org_id)
    return {"message": "Operator successfully deleted"}
