import logging
import uuid
from asyncio import shield
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

import sqlalchemy
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from constants import DEFAULT_ORG_ID
from core.settings import settings

logger = logging.getLogger(__name__)


Base = declarative_base()
engine = create_async_engine(settings.pg_dsn.encoded_string(), echo=settings.debug, future=True)
_async_session = async_sessionmaker(engine, expire_on_commit=False)

if settings.jaeger_trace:
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)


@asynccontextmanager
async def get_session(
    org_id: UUID = DEFAULT_ORG_ID,
) -> AsyncGenerator[AsyncSession]:
    """Dependency that provides an async session for database operations."""

    if org_id is None:
        raise ValueError("org_id must be provided")

    session: AsyncSession = _async_session()
    xid = uuid.uuid4()
    try:
        logger.debug("Transaction BEGIN;", extra={"xid": xid})

        await session.execute(
            sqlalchemy.text("SELECT set_config('app.org_id', :org_id, false)"),
            {"org_id": str(org_id) if isinstance(org_id, UUID) else org_id},
        )

        yield session
        await session.commit()
        logger.debug("Transaction COMMIT;", extra={"xid": xid})

    except DBAPIError as e:
        await session.rollback()
        raise e

    except Exception:
        await session.rollback()
        raise

    finally:
        if session:
            await shield(session.close())
            logger.debug("Connection released to pool")


async def create_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def purge_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
