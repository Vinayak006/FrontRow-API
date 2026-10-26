from fastapi import APIRouter, Depends, Query, Response, status
from sqlmodel import Session

from app.models.user import User
from app.schemas.venue import VenueCreate, VenueRead, VenueUpdate
from app.services.venue import (
    create_venue,
    delete_venue,
    get_venue,
    get_venues,
    update_venue,
)
from app.config.database import get_session
from app.controllers.auth import get_current_user
from app.core.query_param import SearchQuery

venue_router = APIRouter(prefix="/venues", tags=["Venues"])


@venue_router.post(
    "/",
    response_model=VenueRead,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: VenueCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return create_venue(session, data, current_user.id)


@venue_router.get("/", response_model=list[VenueRead])
def list_all(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=10, ge=1, le=50),
    search: SearchQuery | None = None,
    owned_venues: bool = False,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_venues(session, current_user.id, page, per_page, search, owned_venues)


@venue_router.get("/{venue_id}", response_model=VenueRead)
def get_one(
    venue_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return get_venue(session, venue_id, current_user.id)


@venue_router.put("/{venue_id}", response_model=VenueRead)
def update(
    venue_id: int,
    data: VenueUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return update_venue(session, venue_id, data, current_user.id)


@venue_router.delete(
    "/{venue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    venue_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    delete_venue(session, venue_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
