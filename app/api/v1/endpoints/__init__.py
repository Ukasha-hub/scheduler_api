from fastapi import APIRouter
from .filter import router as filter_router
from .user import router as user_router
from .privilege import router as privilege_router 
from .server import router as server_router 
from .slug import router as slug_router 
from .hourly_ad import router as hourly_ad_router 
from .package import router as package_router 

router = APIRouter()

router.include_router(filter_router, prefix="/filters", tags=["Filters"])
router.include_router(user_router, prefix="/users", tags=["Users"])
router.include_router(server_router, prefix="/server", tags=["Servers"])
router.include_router(slug_router, prefix="/slug", tags=["Slug"])
router.include_router(hourly_ad_router, prefix="/hourly-ad", tags=["Hourly Ad"])
router.include_router(package_router, prefix="/package", tags=["Packages"])
