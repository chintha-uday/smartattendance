from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

def normalize_database_url(db_url: str) -> str:
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+psycopg://", 1)
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url

database_url = normalize_database_url(settings.DB_URL)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, pool_pre_ping=True, future=True,
                       connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
