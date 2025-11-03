from fastapi.routing import APIRouter

from .companies import router as companies_router
from .operators import router as operators_router
from .orders import router as orders_router

router = APIRouter()
router.include_router(orders_router, prefix="/orders", tags=["Orders"])
router.include_router(operators_router, prefix="/operators", tags=["Operators"])
router.include_router(companies_router, prefix="/companies", tags=["Companies"])
