from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from app.config.config import settings


def _create_token(
    user_id: int,
    expires_minutes: int,
) -> str:
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
        "iss": "frontrow-api",
        "aud": "frontrow",
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer="frontrow-api",
        audience="frontrow",
        options={"require": ["sub", "iat", "exp", "iss", "aud"]},
    )


def create_access_token(user_id: int) -> str:
    return _create_token(
        user_id,
        settings.JWT_ACCESS_TOKEN_MINUTES,
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        user_id,
        settings.JWT_REFRESH_TOKEN_MINUTES,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    return _decode_token(token)


def decode_refresh_token(token: str) -> dict[str, Any]:
    return _decode_token(token)
