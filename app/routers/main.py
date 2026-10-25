from fastapi import APIRouter

from .user import user_router

main_router = APIRouter(prefix="/v1")

main_router.include_router(user_router)
