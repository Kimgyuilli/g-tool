from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import Base, get_db

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # Import app lazily to avoid triggering lifespan (scheduler)
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
async def sample_user(db_session: AsyncSession):
    """Create a sample user with Google OAuth credentials."""
    from app.mail.models import User

    user = User(
        email="test@example.com",
        google_oauth_token="test_token",
        google_refresh_token="test_refresh",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_mails(db_session: AsyncSession, sample_user):
    """Create sample Gmail and Naver mails."""
    from datetime import UTC, datetime

    from app.mail.models import Mail

    gmail1 = Mail(
        user_id=sample_user.id,
        source="gmail",
        external_id="gmail_123",
        from_email="sender1@example.com",
        from_name="Sender One",
        subject="Test Gmail 1",
        to_email="test@example.com",
        body_text="This is a test Gmail message.",
        received_at=datetime.now(tz=UTC),
        is_read=False,
    )
    gmail2 = Mail(
        user_id=sample_user.id,
        source="gmail",
        external_id="gmail_456",
        from_email="sender2@example.com",
        from_name="Sender Two",
        subject="Test Gmail 2",
        to_email="test@example.com",
        body_text="Another Gmail message.",
        received_at=datetime.now(tz=UTC),
        is_read=True,
    )
    naver1 = Mail(
        user_id=sample_user.id,
        source="naver",
        external_id="naver_789",
        from_email="naver@example.com",
        from_name="Naver Sender",
        subject="Test Naver Mail",
        to_email="test@naver.com",
        body_text="This is a Naver mail.",
        folder="INBOX",
        received_at=datetime.now(tz=UTC),
        is_read=False,
    )
    db_session.add_all([gmail1, gmail2, naver1])
    await db_session.commit()
    await db_session.refresh(gmail1)
    await db_session.refresh(gmail2)
    await db_session.refresh(naver1)
    return {"gmail1": gmail1, "gmail2": gmail2, "naver1": naver1}


@pytest.fixture
async def sample_labels(db_session: AsyncSession, sample_user):
    """Create sample labels for categories."""
    from app.mail.models import Label

    label_work = Label(
        user_id=sample_user.id,
        name="업무",
        color="blue",
        is_default=True,
    )
    label_personal = Label(
        user_id=sample_user.id,
        name="개인",
        color="green",
        is_default=True,
    )
    db_session.add_all([label_work, label_personal])
    await db_session.commit()
    await db_session.refresh(label_work)
    await db_session.refresh(label_personal)
    return {"work": label_work, "personal": label_personal}


@pytest.fixture
async def sample_classification(
    db_session: AsyncSession, sample_mails, sample_labels
):
    """Create a sample classification for the first Gmail mail."""
    from app.mail.models import Classification

    classification = Classification(
        mail_id=sample_mails["gmail1"].id,
        label_id=sample_labels["work"].id,
        confidence=0.9,
    )
    db_session.add(classification)
    await db_session.commit()
    await db_session.refresh(classification)
    return classification
