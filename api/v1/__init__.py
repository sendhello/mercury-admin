from fastapi.routing import APIRouter

from .orders import router as orders_router

router = APIRouter()
router.include_router(orders_router, prefix="/orders", tags=["Orders"])
