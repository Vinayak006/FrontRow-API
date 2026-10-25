from sqlmodel import Session, create_engine

from .config import settings

engine = create_engine(url=settings.DATABASE_URL)


def get_session() -> Session:
    return Session(engine)
