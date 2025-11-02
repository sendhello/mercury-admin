from collections.abc import AsyncGenerator

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi import Depends, Header
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security.http import HTTPBearer
from starlette import status

from core.settings import settings
from db.postgres import AsyncSession, get_session

RULE_PROTECTED_TEXT = "No access to this resource. Please contact your administrator if you believe this is an error."


async def full_protected(
    authorize: AuthJWT = Depends(),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> AuthJWT:
    try:
        await authorize.jwt_required()

    except AuthJWTException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    return authorize


async def multitenancy_protected(
    authorize: AuthJWT = Depends(full_protected),
    x_org_id: str = Header(default=None, alias="X-Org-ID"),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> tuple[AuthJWT, dict, str]:
    """
    Multitenancy-aware protection that validates organization access and sets DB context
    Returns: (authorize, user, org_id)
    """
    # Get user claims and validate multitenancy context
    user_claims = await authorize.get_raw_jwt()

    if x_org_id:
        if x_org_id not in user_claims["org_roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have access to organization {x_org_id}",
            )
        current_org_id = x_org_id

    elif user_claims["org"] is not None:
        current_org_id = user_claims["org"]

    elif user_claims["org_roles"]:
        # If no X-Org-ID header, use the first available organization
        current_org_id = next(iter(user_claims["org_roles"]))

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization context available",
        )

    return authorize, user_claims, current_org_id


async def role_required(
    required_roles: list[str],
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> tuple[AuthJWT, dict, str]:
    """
    Dependency factory for role-based authorization
    Usage: Depends(role_required(["admin", "owner"]))
    """
    authorize, user_claims, org_id = auth_data

    user_roles = user_claims["org_roles"].get(org_id, [])
    if not any(role in user_roles for role in required_roles):
        detail = (
            f"Required roles: {required_roles}. User roles: {user_roles}" if settings.debug else RULE_PROTECTED_TEXT
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    return authorize, user_claims, org_id


async def owner_required(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
):
    authorize, user_claims, org_id = auth_data
    user_roles = user_claims["org_roles"].get(org_id, [])
    if not any(role in user_roles for role in ["owner"]):
        detail = f"Required roles: {["owner"]}. User roles: {user_roles}" if settings.debug else RULE_PROTECTED_TEXT
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    return authorize, user_claims, org_id


async def admin_required(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
):
    authorize, user_claims, org_id = auth_data
    user_roles = user_claims["org_roles"].get(org_id, [])
    if not any(role in user_roles for role in ["admin", "owner"]):
        detail = (
            f"Required roles: {["admin", "owner"]}. User roles: {user_roles}" if settings.debug else RULE_PROTECTED_TEXT
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    return authorize, user_claims, org_id


async def dispatcher_required(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
):
    authorize, user_claims, org_id = auth_data
    user_roles = user_claims["org_roles"].get(org_id, [])
    if not any(role in user_roles for role in ["dispatcher", "admin", "owner"]):
        detail = (
            f"Required roles: {["dispatcher", "admin", "owner"]}. User roles: {user_roles}"
            if settings.debug
            else RULE_PROTECTED_TEXT
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    return authorize, user_claims, org_id


async def courier_required(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
):
    authorize, user_claims, org_id = auth_data
    user_roles = user_claims["org_roles"].get(org_id, [])
    if not any(role in user_roles for role in ["courier", "dispatcher", "admin", "owner"]):
        detail = (
            f"Required roles: {["courier", "dispatcher", "admin", "owner"]}. User roles: {user_roles}"
            if settings.debug
            else RULE_PROTECTED_TEXT
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)

    return authorize, user_claims, org_id


def scope_required(required_scopes: list[str]):
    """
    Dependency factory for scope-based authorization
    Usage: Depends(scope_required(["orders:read", "routes:write"]))
    """

    async def _scope_check(
        auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
    ) -> tuple[AuthJWT, dict, str]:
        authorize, user_claims, org_id = auth_data

        scopes = user_claims["scopes"]
        missing_scopes = [scope for scope in required_scopes if scope not in scopes]
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {missing_scopes}",
            )
        return authorize, user_claims, org_id

    return _scope_check


async def get_org_session(
    auth_data: tuple[AuthJWT, dict, str] = Depends(multitenancy_protected),
) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an AsyncSession bound to the current org_id resolved by multitenancy_protected.

    Example:
        @router.get("/items")
        async def list_items(session: AsyncSession = Depends(get_org_session)):
            ...
    """
    # authorize and user_claims are not needed here, we only extract org_id
    _, _, org_id = auth_data
    async with get_session(org_id) as session:
        yield session
