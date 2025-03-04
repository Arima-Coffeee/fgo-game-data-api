import asyncio
from asyncio.events import AbstractEventLoop
from typing import AsyncGenerator, Generator

import pytest
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from redis.asyncio import Redis  # type: ignore
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.config import Settings
from app.main import app
from app.schemas.common import Region


settings = Settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator[AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for each test case.
    https://github.com/pytest-dev/pytest-asyncio/issues/171
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with LifespanManager(app, startup_timeout=60):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac


@pytest.fixture(scope="session")
async def na_db_conn() -> AsyncGenerator[AsyncConnection, None]:
    engine = create_async_engine(
        settings.data[Region.NA].postgresdsn.replace("postgresql", "postgresql+asyncpg")
    )
    connection = await engine.connect()
    try:
        yield connection
    finally:
        await connection.close()
        await engine.dispose()


@pytest.fixture(scope="session")
async def redis() -> AsyncGenerator[Redis, None]:
    async with Redis.from_url(settings.redisdsn) as redis_client:
        yield redis_client
