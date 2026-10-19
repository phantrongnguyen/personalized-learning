"""Asyncpg migrations; DATABASE_URL is read from settings unless explicitly overridden."""
import asyncio
import os
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from core.config import settings
from models import Base

config = context.config


def run(connection):
    context.configure(connection=connection, target_metadata=Base.metadata,
                      compare_type=True, compare_server_default=True)
    with context.begin_transaction():
        connection.exec_driver_sql("SELECT pg_advisory_xact_lock(1910202601)")
        connection.exec_driver_sql("SET LOCAL lock_timeout = '10s'")
        context.run_migrations()


async def run_async():
    url = config.attributes.get('database_url') or os.getenv('MIGRATION_DATABASE_URL') or settings.async_database_url
    from sqlalchemy.engine import make_url
    url = make_url(url).set(drivername='postgresql+asyncpg')
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.run_sync(run)
    finally:
        await engine.dispose()


if context.is_offline_mode():
    raise RuntimeError('Migrations require an online PostgreSQL connection for baseline/data validation')
elif config.attributes.get('connection') is not None:
    run(config.attributes['connection'])
else:
    asyncio.run(run_async())
