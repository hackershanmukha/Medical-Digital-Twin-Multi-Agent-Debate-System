import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.db.base_class import Base
from app.models import User, Patient, Vitals, Condition, Allergy, Medication, LabReport, Debate
from app.core.security import get_password_hash

# Use a separate test database in-memory for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    # Setup
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async with async_session() as session:
        yield session
        await session.rollback()
        
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    # Create user
    new_user = User(
        email="test_doc@example.com",
        hashed_password=get_password_hash("DocPass123!"),
        role="clinician"
    )
    db_session.add(new_user)
    await db_session.commit()
    
    # Query user
    stmt = select(User).where(User.email == "test_doc@example.com")
    result = await db_session.execute(stmt)
    user = result.scalars().first()
    
    assert user is not None
    assert user.email == "test_doc@example.com"
    assert user.role == "clinician"
    assert user.is_active is True
