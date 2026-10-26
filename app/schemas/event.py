from datetime import date, time, datetime
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

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
    OPEN = "open"


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
