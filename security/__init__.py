# flake8: noqa

from fastapi import Depends

from .auth import (
    admin_required,
    courier_required,
    dispatcher_required,
    full_protected,
    get_org_session,
    multitenancy_protected,
    owner_required,
)


# Legacy protection dependencies
TOKEN_PROTECTED = [Depends(full_protected)]
MULTITENANCY_PROTECTED = [Depends(multitenancy_protected)]
OWNER_REQUIRED = [Depends(owner_required)]
ADMIN_REQUIRED = [Depends(admin_required)]
DISPATCHER_REQUIRED = [Depends(dispatcher_required)]
COURIER_REQUIRED = [Depends(courier_required)]
