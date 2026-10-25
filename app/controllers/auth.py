import jwt
from typing import Any
from fastapi import Cookie, Depends, HTTPException, Response, status
from sqlmodel import Session

from app.models.user import User
from app.utils.token import (
    create_access_token,
    decode_access_token,
    decode_refresh_token,
    create_refresh_token,
)
from app.schemas.user import LoginRequest
from app.services.user import fetch_user_by_email
from app.config.config import settings
from app.utils.password import verify_password
from app.config.database import get_session


def get_current_user(
    response: Response,
    access_token: str | None = Cookie(default=None, alias="frontrow_access"),
    refresh_token: str | None = Cookie(default=None, alias="frontrow_refresh"),
    session: Session = Depends(get_session),
) -> User:
    payload: dict[str, Any] | None = None

    if access_token:
        try:
            payload = decode_access_token(access_token)
        except jwt.ExpiredSignatureError:
            # Access token expired; attempt refresh below.
            pass
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid access token",
            ) from None

    if payload is None:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        try:
            refresh_payload = decode_refresh_token(refresh_token)
            user_id = int(refresh_payload["sub"])
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            ) from None

        payload = {"sub": str(user_id)}

        _refresh_tokens(user_id, response)

    user_id = int(payload["sub"])
    user = session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def authenticate_user(
    session: Session,
    data: LoginRequest,
    response: Response,
) -> User | None:
    user = fetch_user_by_email(session, str(data.email))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password.",
        )

    if not verify_password(data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password.",
        )

    _refresh_tokens(user.id, response)

    return user


def _refresh_tokens(user_id: int, response: Response):
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    response.set_cookie(
        key="frontrow_access",
        value=access_token,
        httponly=not settings.DEVELOPMENT_MODE,
        secure=not settings.DEVELOPMENT_MODE,
        samesite="lax",
        path="/",
        max_age=settings.JWT_ACCESS_TOKEN_MINUTES * 60,
    )

    response.set_cookie(
        key="frontrow_refresh",
        value=refresh_token,
        httponly=not settings.DEVELOPMENT_MODE,
        secure=not settings.DEVELOPMENT_MODE,
        samesite="lax",
        path="/",
        max_age=settings.JWT_REFRESH_TOKEN_MINUTES * 60,
    )
