from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.config.database import get_session
from app.controllers.auth import get_current_user

from app.core.query_param import SearchQuery
from app.models.user import User
from app.schemas.event import (
    EventCreate,
    EventStatus,
    EventUpdate,
    EventRead,
)
from app.services import event as event_service

event_router = APIRouter(prefix="/events", tags=["Events"])


@event_router.post("/", response_model=EventRead)
def create_event(
    data: EventCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EventRead:
    return event_service.create_event(session, data, current_user)


@event_router.get("/", response_model=list[EventRead])
def list_events(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    search: SearchQuery | None = None,
    status: EventStatus | None = None,
    owned: bool = False,
    from_date: date | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[EventRead]:
    return event_service.list_events(
        session,
        page,
        per_page,
        search,
        status,
        owned,
        from_date,
        current_user,
    )


@event_router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EventRead:
    return event_service.get_event(session, event_id, current_user)


@event_router.patch("/{event_id}", response_model=EventRead)
def update_event(
    event_id: int,
    data: EventUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EventRead:
    return event_service.update_event(session, event_id, data, current_user)


@event_router.delete("/{event_id}")
def delete_event(
    event_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return event_service.delete_event(session, event_id, current_user)
