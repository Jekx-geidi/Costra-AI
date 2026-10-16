"""
Run once to create the initial admin user:
    python seed_admin.py
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User
from app.auth.jwt import hash_password


async def main():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        existing = await db.execute(select(User).where(User.email == "admin@geidi.com"))
        if existing.scalar_one_or_none():
            print("Admin user already exists.")
            return
        user = User(
            email="admin@geidi.com",
            hashed_password=hash_password("changeme"),
            role="billing_admin",
        )
        db.add(user)
        await db.commit()
        print("Admin user created: admin@geidi.com / changeme")
        print("CHANGE THIS PASSWORD before any non-local use.")


if __name__ == "__main__":
    import sys
    # psycopg async cannot run on Windows' default ProactorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
