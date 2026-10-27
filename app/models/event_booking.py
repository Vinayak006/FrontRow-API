from datetime import UTC, datetime, date
from typing import Optional, TYPE_CHECKING

from sqlmodel import Column, DateTime, ForeignKey, Relationship, SQLModel, Field

from app.schemas.event import EventBookingStatus

if TYPE_CHECKING:
    from .event import Event
    from .event_seat_claim import EventSeatClaim


class EventBooking(SQLModel, table=True):
    __tablename__ = "event_bookings"

    id: int | None = Field(default=None, primary_key=True)

    event_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "events.id",
                name="fk_event_bookings_event_id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        )
    )

    status: EventBookingStatus = Field(
        default=EventBookingStatus.PENDING,
    )

    event_date: date

    confirmed_at: datetime | None = None

    hold_expires_at: datetime | None = None

    user_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "users.id",
                name="fk_event_bookings_used_by",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
            onupdate=lambda: datetime.now(UTC),
        ),
    )

    event: Optional["Event"] = Relationship()

    seats: list["EventSeatClaim"] = Relationship(
        sa_relationship_kwargs={"order_by": "EventSeatClaim.venue_seat_id"}
    )
