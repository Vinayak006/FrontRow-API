from enum import Enum
from datetime import UTC, datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import (
    CheckConstraint,
    Column,
    DateTime,
    Field,
    ForeignKey,
    Relationship,
    SQLModel,
)

from app.schemas.venue import VenueStatus

if TYPE_CHECKING:
    from .user import User


class Venue(SQLModel, table=True):
    __tablename__ = "venues"

    __table_args__ = (
        CheckConstraint(
            "capacity = rows * columns",
            name="check_venue_capacity",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)

    name: str = Field(nullable=False)
    description: str | None = Field(default=None)

    rows: int = Field(nullable=False, gt=0)
    columns: int = Field(nullable=False, gt=0)
    capacity: int = Field(nullable=False, gt=0)

    owner_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "users.id",
                name="fk_venues_owner_id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )

    contact_email: str = Field(nullable=False)
    contact_mobile: str = Field(nullable=False)

    status: VenueStatus = Field(
        default=VenueStatus.ACTIVE,
        nullable=False,
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

    owner: Optional["User"] = Relationship()
