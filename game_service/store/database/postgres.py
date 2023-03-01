from typing import Optional

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from base.base_accessor import BaseAccessor
from core.settings import Settings

class Base:
    __allow_unmapped__ = True


db = declarative_base(cls=Base, metadata=MetaData(schema=Settings().postgres.db_schema))


class PostgresDatabase(BaseAccessor):
    _engine: Optional[AsyncEngine] = None
    _db: Optional[declarative_base] = None
    session: Optional[AsyncSession] = None

    async def connect(self, *_: list, **__: dict):
        self._db = db
        self._engine = create_async_engine(
            self.app.settings.postgres.dsn, echo=False, future=True
        )
        self.session = sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)
        self.logger.info("Connected to Postgres")

    async def disconnect(self, *_: list, **__: dict):
        if self._engine:
            await self._engine.dispose()
        self.logger.info("Disconnected from Postgres")
