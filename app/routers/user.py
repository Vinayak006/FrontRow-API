from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from app.models.user import User
from app.schemas.user import LoginRequest, RegisterRequest, UserResponse, UserInfo
from app.services.user import (
    create_user,
    signout_user,
)
from app.controllers.auth import get_current_user, authenticate_user
from app.config.database import get_session

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.get("/me", response_model=UserInfo)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@user_router.post("/register", response_model=UserResponse)
def register(
    data: RegisterRequest,
    session: Session = Depends(get_session),
):
    return create_user(session, data)


@user_router.post("/login", response_model=UserInfo)
def login(
    data: LoginRequest,
    response: Response,
    session: Session = Depends(get_session),
):
    return authenticate_user(session, data, response)


@user_router.post("/signout")
def signout_route(response: Response) -> Response:
    return signout_user(response)
