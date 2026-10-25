import jwt
from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError


import logging
from app.models import User
from app.utils.token import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.schemas.user import RegisterRequest, LoginRequest, UserResponse
from app.config.config import settings
from app.utils.password import hash_password, verify_password
from app.config.database import get_session

logger = logging.getLogger(__name__)


def create_user(session: Session, data: RegisterRequest) -> UserResponse:
    existing_user = fetch_user_by_email(session, str(data.email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    user = User(
        email=str(data.email),
        password=hash_password(data.password),
        name=data.name,
    )
    try:
        session.add(user)
        session.commit()
    except IntegrityError as e:
        session.rollback()
        logger.exception(msg=e)
        constraint = getattr(
            getattr(e.orig, "diag", None),
            "constraint_name",
            None,
        )
        if constraint == "ix_users_email":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered.",
            ) from e
        raise HTTPException(
            status_code=409,
            detail="Something went wrong while creating user.",
        )
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while creating user.",
        )
    return user


def fetch_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).one_or_none()


def signout_user(response: Response) -> Response:
    response.delete_cookie(
        key="frontrow_access",
        path="/",
        httponly=not settings.DEVELOPMENT_MODE,
        secure=not settings.DEVELOPMENT_MODE,
        samesite="lax",
    )

    response.delete_cookie(
        key="frontrow_refresh",
        path="/",
        httponly=not settings.DEVELOPMENT_MODE,
        secure=not settings.DEVELOPMENT_MODE,
        samesite="lax",
    )

    response.status_code = status.HTTP_204_NO_CONTENT

    return response
