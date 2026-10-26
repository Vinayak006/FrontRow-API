from enum import Enum
from pydantic import ConfigDict, EmailStr, Field, model_validator, BaseModel

from app.schemas.user import UserInfo


class VenueStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class VenueCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    rows: int = Field(gt=0)
    columns: int = Field(gt=0)
    capacity: int = Field(gt=0)
    contact_email: EmailStr
    contact_mobile: str = Field(min_length=1)
    status: VenueStatus = VenueStatus.ACTIVE

    @model_validator(mode="after")
    def validate_capacity(self):
        if self.capacity != self.rows * self.columns:
            raise ValueError("Capacity must equal rows × columns")
        return self


class VenueUpdate(VenueCreate):
    pass


class VenueRead(BaseModel):

    id: int
    name: str
    description: str | None
    rows: int
    columns: int
    capacity: int
    owner: UserInfo
    contact_email: EmailStr
    contact_mobile: str
    status: VenueStatus

    model_config = ConfigDict(from_attributes=True)
