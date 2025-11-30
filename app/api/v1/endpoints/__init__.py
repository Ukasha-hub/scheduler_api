from fastapi import APIRouter
from .filter import router as filter_router

router = APIRouter()

router.include_router(filter_router, prefix="/filters", tags=["Filters"])
