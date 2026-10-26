# models/event_seat.py

from datetime import UTC, date, datetime

from sqlmodel import Column, DateTime, ForeignKey, SQLModel, Field

from app.schemas.event import EventSeatStatus


class EventSeat(SQLModel, table=True):
    __tablename__ = "event_seats"

    id: int | None = Field(default=None, primary_key=True)

    event_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "events.id",
                name="fk_event_seats_event_id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        )
    )

    status: EventSeatStatus = Field(
        default=EventSeatStatus.OPEN,
    )

    reserved_at: datetime | None = None

    reserved_by: int = Field(
        sa_column=Column(
            ForeignKey(
                "users.id",
                name="fk_event_seats_reserved_by",
                ondelete="CASCADE",
            ),
            nullable=True,
        )
    )

    hold_at: date | None = None

    hold_by: int = Field(
        sa_column=Column(
            ForeignKey(
                "users.id",
                name="fk_event_seats_hold_by",
                ondelete="CASCADE",
            ),
            nullable=True,
        )
    )

    hold_expires_at: datetime | None = None

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
