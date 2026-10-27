from datetime import date, time, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from fastapi import HTTPException
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.user import UserInfo
from app.schemas.venue import VenueRead

EventCategory = Literal[
    "entertainment",
    "education",
    "comedy-show",
    "music-concert",
]

EventStatus = Literal["active", "inactive"]


class EventSeatStatus(str, Enum):
    RESERVED = "reserved"
    AVAILABLE = "available"
    HOLD = "hold"


class EventBookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class EventBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    base_price: Decimal = Field(ge=0, max_digits=10, decimal_places=2)

    venue_id: int = Field(gt=0)

    from_date: date
    to_date: date
    from_time: time
    to_time: time

    location: str = Field(min_length=1, max_length=500)
    status: EventStatus = "active"
    contact_email: EmailStr
    contact_mobile: str = Field(min_length=1, max_length=20)
    category: EventCategory

    @model_validator(mode="after")
    def validate_event_dates(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date must be on or after from_date")

        if self.to_date == self.from_date and self.to_time <= self.from_time:
            raise ValueError(
                "to_time must be later than from_time for a same-day event"
            )

        return self


class EventCreate(EventBase):
    pass


class EventUpdate(EventBase):
    pass


class EventRead(BaseModel):
    id: int
    name: str
    description: str | None
    base_price: Decimal

    venue: VenueRead
    organizer: UserInfo

    from_date: date
    to_date: date
    from_time: time
    to_time: time

    location: str
    status: EventStatus
    contact_email: str
    contact_mobile: str
    category: EventCategory

    created_at: datetime
    updated_at: datetime


class EventSeatInfo(BaseModel):
    id: int
    seat_number: str
    status: EventSeatStatus | None = EventSeatStatus.AVAILABLE


class EventSeatHoldRequest(BaseModel):
    seat_ids: list[int] = Field(min_length=1)
    event_date: date

    @field_validator("seat_ids")
    @classmethod
    def validate_duplicate_seat_ids(cls, v: str) -> str:
        if len(v) != len(set(v)):
            raise HTTPException(
                status_code=400,
                detail="Duplicate seat IDs are not allowed",
            )
        return v


class EventBookingIDResponse(BaseModel):
    booking_id: int


class EventBookingDetail(BaseModel):
    id: int
    event_date: date
    hold_expires_at: datetime | None
    status: EventBookingStatus
    event: EventRead
    seats: list[EventSeatInfo]
