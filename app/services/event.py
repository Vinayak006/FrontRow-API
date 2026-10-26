from datetime import UTC, date, datetime
from math import ceil
import logging
from fastapi import HTTPException, status
from psycopg.errors import ForeignKeyViolation
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, insert, select

from app.models.user import User
from app.models.event import Event
from app.models.event_seat import EventSeat
from app.models.venue import Venue
from app.schemas.event import (
    EventCreate,
    EventRead,
    EventUpdate,
)

logger = logging.getLogger(__name__)


def create_event(session: Session, data: EventCreate, current_user: User) -> EventRead:
    event = Event(**data.model_dump(), organizer_id=current_user.id)

    venue = session.get(Venue, data.venue_id)

    if not venue:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Venue not found",
        )

    session.add(event)

    try:
        session.flush()

        session.exec(
            insert(EventSeat),
            params=[
                {
                    "event_id": event.id,
                    "status": "OPEN",
                    "created_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
                for _ in range(venue.capacity)
            ],
        )

        session.commit()
    except IntegrityError as ie:
        session.rollback()
        logger.exception(msg=ie)
        message = ""
        if isinstance(ie.orig, ForeignKeyViolation):
            message = "Failed to create event due to integrity error"
            constraint = ie.orig.diag.constraint_name
            if constraint == "fk_events_venue_id":
                message = "Invalid venue"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=400,
            detail="Something went wrong while creating event",
        )

    return event


def list_events(
    session: Session,
    page: int,
    per_page: int,
    search: str | None,
    status: str | None,
    owned: bool,
    from_date: date | None,
    current_user: User,
) -> list[EventRead]:

    statement = select(Event)

    if from_date:
        statement = statement.where(Event.from_date >= from_date)

    if owned:
        statement = statement.where(Event.organizer_id == current_user.id)

    if search:
        statement = statement.where(Event.name.icontains(search))

    if status:
        statement = statement.where(Event.status == status)

    statement = (
        statement.order_by(Event.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    return session.exec(statement).all()


def get_event(session: Session, event_id: int, current_user: User) -> Event:
    event = session.exec(
        select(Event).where(Event.id == event_id, Event.organizer_id == current_user.id)
    ).one_or_none()

    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    return event


def update_event(
    session: Session,
    event_id: int,
    data: EventUpdate,
    current_user: User,
) -> EventRead:
    event = get_event(session, event_id, current_user)
    event.sqlmodel_update(data.model_dump())

    try:
        session.commit()
    except IntegrityError as ie:
        session.rollback()
        logger.exception(msg=ie)
        message = ""
        if isinstance(ie.orig, ForeignKeyViolation):
            message = "Failed to create event due to integrity error"
            constraint = ie.orig.diag.constraint_name
            if constraint == "fk_events_venue_id":
                message = "Invalid venue"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=400,
            detail="Something went wrong while updating event",
        )

    return event


def delete_event(session: Session, event_id: int, current_user: User):
    event = get_event(session, event_id, current_user)

    session.delete(event)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=400,
            detail="Something went wrong while deleting event",
        )
