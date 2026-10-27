from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import (
    Column,
    DateTime,
    ForeignKey,
    Relationship,
    SQLModel,
    Field,
    UniqueConstraint,
)

if TYPE_CHECKING:
    from .venue_seat import VenueSeat


class EventSeatClaim(SQLModel, table=True):
    __tablename__ = "event_seat_claims"

    __table_args__ = (
        UniqueConstraint(
            "venue_seat_id",
            "event_id",
            "event_date",
            name="uq_event_seat_claims_seat_event_date",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    venue_seat_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "venue_seats.id",
                name="fk_event_seat_claims_seat_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    event_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "events.id",
                name="fk_event_seat_claims_event_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    booking_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "event_bookings.id",
                name="fk_event_seat_claims_booking_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    event_date: date

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

    venue_seat: Optional["VenueSeat"] = Relationship()
