from datetime import UTC, date, datetime, time, timedelta
import logging

from sqlalchemy.orm import joinedload, selectinload
from fastapi import HTTPException, status
from psycopg.errors import ForeignKeyViolation
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, and_, delete, select, text, update

from app.config.config import settings
from app.models.event_seat_claim import EventSeatClaim
from app.models.event_booking import EventBooking
from app.models.user import User
from app.models.event import Event
from app.models.venue_seat import VenueSeat
from app.models.venue import Venue
from app.schemas.event import (
    EventCreate,
    EventBookingDetail,
    EventRead,
    EventBookingIDResponse,
    EventSeatInfo,
    EventSeatStatus,
    EventStatus,
    EventUpdate,
    EventBookingStatus,
)

logger = logging.getLogger(__name__)


def _check_for_venue_conflict(
    session: Session,
    venue_id: int,
    to_date: date,
    from_date: date,
    to_time: time,
    from_time: time,
):
    session.exec(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
        params={"key": f"create_event:{venue_id}"},
    )

    conflicting_event = session.exec(
        select(Event.id).where(
            Event.venue_id == venue_id,
            Event.status == "active",
            Event.from_date <= to_date,
            Event.to_date >= from_date,
            Event.from_time < to_time,
            Event.to_time > from_time,
        )
    ).first()

    if conflicting_event:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Venue is already booked for the selected date and time",
        )


def create_event(session: Session, data: EventCreate, current_user: User) -> EventRead:

    try:
        venue = session.get(Venue, data.venue_id)

        if not venue:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Venue not found",
            )

        _check_for_venue_conflict(
            session,
            data.venue_id,
            data.to_date,
            data.from_date,
            data.to_time,
            data.from_time,
        )

        event = Event(**data.model_dump(), organizer_id=current_user.id)

        session.add(event)

        session.commit()

        return event

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
    except HTTPException as he:
        session.rollback()
        logger.exception(msg=he)
        raise
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=400,
            detail="Something went wrong while creating event",
        )


def list_events(
    session: Session,
    page: int,
    per_page: int,
    search: str | None,
    status: str | None,
    owned: bool,
    booked: bool,
    from_date: date | None,
    current_user: User,
) -> list[EventRead]:

    statement = select(Event)

    if from_date:
        statement = statement.where(Event.from_date >= from_date)

    if owned:
        statement = statement.where(Event.organizer_id == current_user.id)

    if booked:
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


def get_event_detail(session: Session, event_id: int) -> Event:
    return _get_event(session, event_id)


def _get_event(
    session: Session, event_id: int, organizer_id: int | None = None
) -> Event:
    event_q = select(Event).where(Event.id == event_id)

    if organizer_id:
        event_q = event_q.where(Event.organizer_id == organizer_id)

    event = session.exec(event_q).one_or_none()

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
    try:
        _check_for_venue_conflict(
            session,
            data.venue_id,
            data.to_date,
            data.from_date,
            data.to_time,
            data.from_time,
        )
        event = _get_event(session, event_id, current_user.id)
        event.sqlmodel_update(data.model_dump())

        session.commit()
        return event
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
    except HTTPException as he:
        session.rollback()
        logger.exception(msg=he)
        raise
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=400,
            detail="Something went wrong while updating event",
        )


def delete_event(session: Session, event_id: int, current_user: User):
    event = _get_event(session, event_id, current_user.id)

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


def _effective_seat_status(
    booking_status: EventBookingStatus | None,
    hold_expires_at: datetime | None,
    now: datetime,
) -> EventSeatStatus:
    """Seat state follows its booking; a lapsed pending hold means free."""
    if booking_status == EventBookingStatus.CONFIRMED:
        return EventSeatStatus.RESERVED

    if (
        booking_status == EventBookingStatus.PENDING
        and hold_expires_at is not None
        and hold_expires_at > now
    ):
        return EventSeatStatus.HOLD

    return EventSeatStatus.AVAILABLE


def get_event_seats(
    session: Session,
    event_id: int,
    event_date: date,
) -> list[EventSeatInfo]:
    venue_id = session.exec(
        select(Event.venue_id).where(
            Event.id == event_id,
            Event.from_date <= event_date,
            Event.to_date >= event_date,
        )
    ).first()

    if venue_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    rows = session.exec(
        select(
            VenueSeat.id,
            VenueSeat.seat_number,
            EventBooking.status,
            EventBooking.hold_expires_at,
        )
        .outerjoin(
            EventSeatClaim,
            and_(
                EventSeatClaim.venue_seat_id == VenueSeat.id,
                EventSeatClaim.event_id == event_id,
                EventSeatClaim.event_date == event_date,
            ),
        )
        .outerjoin(EventBooking, EventBooking.id == EventSeatClaim.booking_id)
        .where(VenueSeat.venue_id == venue_id)
        .order_by(VenueSeat.id)
    ).all()

    now = datetime.now(UTC)

    return [
        EventSeatInfo(
            id=seat_id,
            seat_number=seat_number,
            status=_effective_seat_status(booking_status, hold_expires_at, now),
        )
        for seat_id, seat_number, booking_status, hold_expires_at in rows
    ]


def hold_event_seats(
    session: Session,
    event_id: int,
    event_date: date,
    seat_ids: list[int],
    user_id: int,
) -> EventBookingIDResponse:
    try:

        event = session.get(Event, event_id)

        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        if not event.from_date <= event_date <= event.to_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event is not scheduled on the selected date",
            )

        seats = session.exec(
            select(VenueSeat.id).where(
                VenueSeat.venue_id == event.venue_id,
                VenueSeat.id.in_(seat_ids),
            )
        ).all()

        if len(seats) != len(seat_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="One or more seats do not exist for this event",
            )
        now = datetime.now(UTC)

        session.exec(
            delete(EventBooking).where(
                EventBooking.status == EventBookingStatus.PENDING,
                EventBooking.hold_expires_at <= now,
                EventBooking.id.in_(
                    select(EventSeatClaim.booking_id).where(
                        EventSeatClaim.event_id == event_id,
                        EventSeatClaim.event_date == event_date,
                        EventSeatClaim.venue_seat_id.in_(seat_ids),
                    )
                ),
            )
        )

        expires_at = now + timedelta(minutes=settings.RESERVE_HOLD_MIN)

        booking = EventBooking(
            event_id=event_id,
            user_id=user_id,
            event_date=event_date,
            status=EventBookingStatus.PENDING,
            hold_expires_at=expires_at,
        )

        session.add(booking)
        session.flush()

        claimed_seat_ids = session.scalars(
            pg_insert(EventSeatClaim)
            .values(
                [
                    {
                        "venue_seat_id": seat_id,
                        "event_id": event_id,
                        "booking_id": booking.id,
                        "event_date": event_date,
                        "created_at": now,
                        "updated_at": now,
                    }
                    for seat_id in sorted(seat_ids)
                ]
            )
            .on_conflict_do_nothing(constraint="uq_event_seat_claims_seat_event_date")
            .returning(EventSeatClaim.venue_seat_id)
        ).all()

        if len(claimed_seat_ids) != len(seat_ids):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="One or more seats are already held or booked",
            )

        session.commit()

        return EventBookingIDResponse(booking_id=booking.id)

    except HTTPException:
        session.rollback()
        raise

    except Exception:
        session.rollback()
        logger.exception(
            "Failed to hold seats for event_id=%s, event_date=%s",
            event_id,
            event_date,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while holding seats",
        )


def checkout_event_seats(
    session: Session,
    booking_id: int,
    user_id: int,
) -> EventBookingIDResponse:
    try:
        now = datetime.now(UTC)

        confirmed_id = session.scalars(
            update(EventBooking)
            .where(
                EventBooking.id == booking_id,
                EventBooking.user_id == user_id,
                EventBooking.status == EventBookingStatus.PENDING,
                EventBooking.hold_expires_at > now,
            )
            .values(
                status=EventBookingStatus.CONFIRMED,
                confirmed_at=now,
                hold_expires_at=None,
            )
            .returning(EventBooking.id)
        ).one_or_none()

        if confirmed_id is None:
            owned = session.exec(
                select(EventBooking.id).where(
                    EventBooking.id == booking_id,
                    EventBooking.user_id == user_id,
                )
            ).first()

            if owned is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Booking not found",
                )

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Seat hold has expired or the booking is already confirmed",
            )

        session.commit()

        return EventBookingIDResponse(booking_id=booking_id)

    except HTTPException as he:
        session.rollback()
        logger.exception(msg=he)
        raise

    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong during checkout",
        )


def get_booking_detail(
    session: Session, booking_id: int, user_id: int
) -> EventBookingDetail:
    db_event_booking = session.exec(
        select(EventBooking)
        .where(EventBooking.id == booking_id, EventBooking.user_id == user_id)
        .options(
            joinedload(EventBooking.event).options(
                joinedload(Event.venue),
                joinedload(Event.organizer),
            ),
            selectinload(EventBooking.seats).joinedload(EventSeatClaim.venue_seat),
        )
    ).one_or_none()

    if not db_event_booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found"
        )

    now = datetime.now(UTC)

    if (
        db_event_booking.status == EventBookingStatus.PENDING
        and db_event_booking.hold_expires_at is not None
        and db_event_booking.hold_expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or expired",
        )

    seat_status = _effective_seat_status(
        db_event_booking.status, db_event_booking.hold_expires_at, now
    )

    return EventBookingDetail(
        id=db_event_booking.id,
        event_date=db_event_booking.event_date,
        status=db_event_booking.status,
        event=EventRead.model_validate(db_event_booking.event, from_attributes=True),
        seats=[
            EventSeatInfo(
                id=claim.venue_seat_id,
                seat_number=claim.venue_seat.seat_number,
                status=seat_status,
            )
            for claim in db_event_booking.seats
        ],
    )
