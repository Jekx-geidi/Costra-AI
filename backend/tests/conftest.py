"""
Shared fixtures for API-level tests.

API tests run against a separate PostgreSQL database (never the dev database):
TEST_DATABASE_URL if set, otherwise DATABASE_URL with the database name suffixed
"_test". When that database is unreachable those tests are skipped, so the pure
unit tests still run anywhere.
"""
import asyncio
import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

if sys.platform == "win32":
    # psycopg's async driver cannot run on Windows' default ProactorEventLoop.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.auth.dependencies import ROLES
from app.auth.jwt import create_access_token
from app.config import settings
from app.database import Base, get_db
from app.main import app as api
from app.models.user import User


def _test_database_url() -> str:
    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]
    url = make_url(settings.database_url)
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


# Probe the test database once per run; without this every API test pays its own connect timeout.
_db_unavailable: str | None = None
_db_checked = False


@pytest.fixture
async def db_engine():
    global _db_unavailable, _db_checked
    if _db_unavailable:
        pytest.skip(_db_unavailable)
    engine = create_async_engine(_test_database_url(), poolclass=NullPool, connect_args={"connect_timeout": 3})
    try:
        async with engine.begin() as conn:
            if not _db_checked:
                await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # unreachable server, missing database, bad credentials
        await engine.dispose()
        _db_unavailable = f"test database not available: {exc.__class__.__name__}"
        pytest.skip(_db_unavailable)
    _db_checked = True
    yield engine
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} CASCADE"))
    await engine.dispose()


@pytest.fixture
def session_factory(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def db(session_factory):
    """A session for arranging data and asserting on results directly."""
    async with session_factory() as session:
        yield session


@pytest.fixture
async def client(session_factory, tmp_path, monkeypatch):
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    api.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(settings, "invoice_storage_path", str(tmp_path / "invoices"))
    async with AsyncClient(transport=ASGITransport(app=api), base_url="http://test") as c:
        yield c
    api.dependency_overrides.clear()


@pytest.fixture
async def auth(session_factory):
    """Authorization headers for one active user per role, e.g. auth['viewer']."""
    async with session_factory() as session:
        for role in ROLES:
            session.add(User(email=f"{role}@test.geidi", hashed_password="unused", role=role))
        await session.commit()
    return {
        role: {"Authorization": f"Bearer {create_access_token(subject=f'{role}@test.geidi', role=role)}"}
        for role in ROLES
    }
