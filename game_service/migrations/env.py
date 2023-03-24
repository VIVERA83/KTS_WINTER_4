import asyncio
from logging.config import fileConfig

from alembic import context
from core.settings import Settings
from icecream import ic
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine
from store.database.postgres import GameBase

config = context.config
settings = Settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = GameBase.metadata
config.set_main_option("sqlalchemy.url", settings.postgres.dsn)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )
    current_tenant = settings.postgres.db_schema
    ic(current_tenant)
    async with connectable.connect() as connection:
        await connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS %s" % current_tenant)
        )
        await connection.commit()
        await connection.execute(text('set search_path to "%s"' % current_tenant))
        await connection.commit()
        connection.dialect.default_schema_name = current_tenant
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
