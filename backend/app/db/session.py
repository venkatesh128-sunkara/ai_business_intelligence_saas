from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

_database_url = settings.DATABASE_URL

if _database_url.startswith("postgresql://") and "+psycopg" not in _database_url:
    _database_url = _database_url.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {}
if _database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(_database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
