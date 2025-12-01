from fastapi import APIRouter
from .filter import router as filter_router
from .user import router as user_router
from .privilege import router as privilege_router 

router = APIRouter()

router.include_router(filter_router, prefix="/filters", tags=["Filters"])
router.include_router(user_router, prefix="/users", tags=["Users"])

