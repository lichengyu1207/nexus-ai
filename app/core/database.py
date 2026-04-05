from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# 使用同步SQLite连接
engine = create_engine(
    settings.DATABASE_URL.replace('sqlite+aiosqlite:///', 'sqlite:///'),
    echo=False,
    future=True
)

SessionLocal = sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()