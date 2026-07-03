from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Erstellt alle Tabellen (nur für Entwicklung; in Produktion: Alembic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

from datetime import date as _date
from sqlalchemy import and_ as _and_

def aktives_mitglied_filter():
    """
    Standardfilter für aktive Mitglieder:
    - nicht soft-deleted (deleted_at IS NULL)
    - Mitgliedschaft nicht abgelaufen (mitglied_bis IS NULL oder in der Zukunft)
    
    Verwendung: .where(aktives_mitglied_filter())
    """
    from app.models import Mitglied
    return _and_(
        Mitglied.deleted_at.is_(None),
        (Mitglied.mitglied_bis.is_(None)) | (Mitglied.mitglied_bis >= _date.today())
    )
