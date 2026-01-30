import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Строка подключения для SQLite (sync)
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "sqlite:///ecommerce.db")

# Создаём Engine
engine = create_engine(SYNC_DATABASE_URL, echo=True)

# Настраиваем фабрику сеансов
SessionLocal = sessionmaker(bind=engine)


# --------------- Асинхронное подключение к PostgreSQL -------------------------

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# Строка подключения для PostgreSQL (async)
ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://shop:shop@db:5432/shop",
)

# Создаём Engine
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# Настраиваем фабрику сеансов
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
