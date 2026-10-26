from datetime import UTC, date, time, datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from sqlmodel import Column, DateTime, ForeignKey, Relationship, SQLModel, Field

if TYPE_CHECKING:
    from .user import User
    from .venue import Venue


class Event(SQLModel, table=True):
    __tablename__ = "events"

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(index=True, max_length=255)
    description: Optional[str] = None

    base_price: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        ge=0,
    )

    venue_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "venues.id",
                name="fk_events_venue_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )
    organizer_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "users.id",
                name="fk_events_organizer_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    from_date: date
    to_date: date
    from_time: time
    to_time: time

    location: str

    status: str = Field(default="active", index=True)

    contact_email: str
    contact_mobile: str

    category: str

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

    venue: Optional["Venue"] = Relationship()
    organizer: Optional["User"] = Relationship()
