from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
import logging

from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueRead, VenueUpdate

logger = logging.getLogger()


def create_venue(
    session: Session,
    data: VenueCreate,
    owner_id: int,
) -> VenueRead:
    venue = Venue(
        **data.model_dump(),
        owner_id=owner_id,
    )

    session.add(venue)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Something went wrong while creating venue.",
        )

    return venue


def get_venues(
    session: Session,
    owner_id: int,
    page: int,
    per_page: int,
    search: str | None,
    owned_venues: bool,
) -> list[VenueRead]:
    statement = select(Venue)

    if owned_venues:
        statement = statement.where(Venue.owner_id == owner_id)

    if search:
        statement = statement.where(Venue.name.icontains(search))

    statement = (
        statement.order_by(Venue.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )

    return session.exec(statement).all()


def get_venue(
    session: Session,
    venue_id: int,
    owner_id: int,
) -> Venue:
    statement = select(Venue).where(
        Venue.id == venue_id,
        Venue.owner_id == owner_id,
    )
    venue = session.exec(statement).one_or_none()

    if venue is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found"
        )

    return venue


def update_venue(
    session: Session,
    venue_id: int,
    data: VenueUpdate,
    owner_id: int,
) -> VenueRead:
    venue = get_venue(session, venue_id, owner_id)

    venue.sqlmodel_update(data.model_dump())

    session.add(venue)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=400,
            detail="Something went wrong while updating venue",
        )

    return venue


def delete_venue(
    session: Session,
    venue_id: int,
    owner_id: int,
) -> None:
    venue = get_venue(session, venue_id, owner_id)

    session.delete(venue)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.exception(msg=e)
        raise HTTPException(
            status_code=409,
            detail="Something went wrong while deleting venue",
        )
