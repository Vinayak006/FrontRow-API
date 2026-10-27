from datetime import UTC, datetime

from sqlmodel import Column, DateTime, ForeignKey, SQLModel, Field


class VenueSeat(SQLModel, table=True):
    __tablename__ = "venue_seats"

    id: int | None = Field(default=None, primary_key=True)

    venue_id: int = Field(
        sa_column=Column(
            ForeignKey(
                "venues.id",
                name="fk_venue_seats_venue_id",
                ondelete="CASCADE",
            ),
            index=True,
            nullable=False,
        )
    )

    seat_number: str

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
