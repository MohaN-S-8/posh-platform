"""
Seed script — run once to populate reference data.
Run with: python -m app.db.seed
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "mysql+asyncmy://posh_user:changeme_password@localhost:3306/posh_db",
)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with AsyncSessionLocal() as db:
        # ── 1. Roles ──────────────────────────────────────────────────────
        await db.execute(
            text("""
                INSERT IGNORE INTO role_master (role_id, role_name)
                VALUES
                    (1, 'Super Admin'),
                    (2, 'Company Admin'),
                    (3, 'HR'),
                    (4, 'Employee')
            """)
        )

        # ── 2. Default company (needed for signup FK) ─────────────────────
        await db.execute(
            text("""
                INSERT IGNORE INTO company_master
                    (company_id, company_code, company_name, status)
                VALUES
                    (1, 'DEFAULT', 'Default Company', 'Active')
            """)
        )

        await db.commit()
        print("✅ Seed complete — roles and default company inserted.")


if __name__ == "__main__":
    asyncio.run(seed())