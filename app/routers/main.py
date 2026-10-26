from fastapi import APIRouter

from .user import user_router
from .venue import venue_router
from .event import event_router

main_router = APIRouter(prefix="/v1")

main_router.include_router(user_router)
main_router.include_router(venue_router)
main_router.include_router(event_router)
