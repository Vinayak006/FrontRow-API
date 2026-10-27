from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.config.database import get_session
from app.controllers.auth import get_current_user

from app.core.query_param import SearchQuery
from app.models.user import User
from app.schemas.event import (
    EventBookingDetail,
    EventCreate,
    EventSeatHoldRequest,
    EventBookingIDResponse,
    EventSeatInfo,
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


@event_router.post(
    "/{event_id}/seats/hold",
    response_model=EventBookingIDResponse,
)
def hold_event_seats(
    event_id: int,
    data: EventSeatHoldRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EventBookingIDResponse:
    return event_service.hold_event_seats(
        session=session,
        event_id=event_id,
        event_date=data.event_date,
        seat_ids=data.seat_ids,
        user_id=current_user.id,
    )


@event_router.post(
    "/booking/{booking_id}/checkout", response_model=EventBookingIDResponse
)
def checkout_booking(
    booking_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EventBookingIDResponse:
    return event_service.checkout_event_seats(
        session=session,
        booking_id=booking_id,
        user_id=current_user.id,
    )


@event_router.get("/", response_model=list[EventRead])
def list_events(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    search: SearchQuery | None = None,
    status: EventStatus | None = None,
    owned: bool = False,
    booked: bool = False,
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
        booked,
        from_date,
        current_user,
    )


@event_router.get("/booking/{booking_id}", response_model=EventBookingDetail)
def get_event_booking_detail(
    booking_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> EventBookingDetail:
    return event_service.get_booking_detail(session, booking_id, current_user.id)


@event_router.get(
    "/{event_id}/seats",
    response_model=list[EventSeatInfo],
)
def get_event_seats(
    event_id: int,
    event_date: date,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[EventSeatInfo]:
    return event_service.get_event_seats(session, event_id, event_date)


@event_router.get("/{event_id}", response_model=EventRead)
def get_event(
    event_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_user),
) -> EventRead:
    return event_service.get_event_detail(session, event_id)


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
