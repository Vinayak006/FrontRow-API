from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    name: str | None = None


class UserResponse(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class UserInfo(BaseModel):
    id: int
    name: str | None = None
    email: str

    model_config = ConfigDict(from_attributes=True)
