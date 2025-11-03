from uuid import UUID

from async_fastapi_jwt_auth import AuthJWT
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy import select

from db.postgres import get_session
from models import Company
from schemas import CompanyCreate, CompanyResponse, CompanyUpdate
from security import DISPATCHER_REQUIRED, multitenancy_protected

router = APIRouter()


@router.post("/", response_model=CompanyResponse, summary="Create company", dependencies=DISPATCHER_REQUIRED)
async def create_company(
    company_data: CompanyCreate,
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> CompanyResponse:
    _, _, org_id = auth_data
    async with get_session(org_id) as session:
        company = Company(**company_data.model_dump(exclude_none=True))
        session.add(company)
        await session.flush()
        await session.commit()
        await session.refresh(company)
    return CompanyResponse.model_validate(company, from_attributes=True)


@router.get(
    "/",
    response_model=list[CompanyResponse],
    summary="List companies",
)
async def list_companies(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> list[CompanyResponse]:
    _, _, org_id = auth_data
    async with get_session(org_id) as session:
        result = await session.execute(select(Company))
        companies = result.scalars().all()
    return [CompanyResponse.model_validate(i, from_attributes=True) for i in companies]


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get company by ID",
    dependencies=DISPATCHER_REQUIRED,
)
async def get_company_by_id(
    company_id: UUID = Path(description="ID of the company to retrieve"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> CompanyResponse:
    _, _, org_id = auth_data
    company = await Company.get_by_id(company_id, current_org=org_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return CompanyResponse.model_validate(company, from_attributes=True)


@router.put(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Update company",
    dependencies=DISPATCHER_REQUIRED,
)
async def update_company(
    company_data: CompanyUpdate,
    company_id: UUID = Path(description="ID of the company to update"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> CompanyResponse:
    _, _, org_id = auth_data
    company = await Company.get_by_id(company_id, current_org=org_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = company_data.model_dump(exclude_unset=True)
    company = await company.update(current_org=org_id, **update_data)
    return CompanyResponse.model_validate(company, from_attributes=True)


@router.delete(
    "/{company_id}",
    summary="Delete company",
    dependencies=DISPATCHER_REQUIRED,
)
async def delete_company(
    company_id: UUID = Path(description="ID of the company to delete"),
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> dict:
    _, _, org_id = auth_data
    company = await Company.get_by_id(company_id, current_org=org_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await company.delete(current_org=org_id)
    return {"message": "Company successfully deleted"}
