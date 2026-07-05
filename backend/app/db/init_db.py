import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import engine
from app.db.base_class import Base
from app.models import User
from app.core.security import get_password_hash

async def init_db() -> None:
    """Initialize database tables and seed initial clinician user."""
    # 1. Create tables
    async with engine.begin() as conn:
        # In production, use Alembic migrations instead of create_all
        await conn.run_sync(Base.metadata.create_all)
    
    # 2. Seed initial clinician user
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalars().first()
        
        if not user:
            # Create a default clinician account
            default_clinician = User(
                email="clinician@medicalai.com",
                hashed_password=get_password_hash("ClinicianPass123!"),
                role="clinician",
                is_active=True
            )
            session.add(default_clinician)
            await session.commit()
            print("Successfully seeded default clinician user: clinician@medicalai.com")
        else:
            print("Database already contains users. Seeding skipped.")

if __name__ == "__main__":
    print("Initializing database...")
    asyncio.run(init_db())
