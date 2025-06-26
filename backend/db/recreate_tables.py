import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import AsyncSessionLocal
from backend.models.sales_models import Base
from backend.models.csv_row import CsvRow
from sqlalchemy import text

async def recreate_tables():
    async with AsyncSessionLocal() as session:
        # Drop all tables
        await session.execute(text("DROP TABLE IF EXISTS sales_user_requirements CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS sales_search_messages CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS sales_users CASCADE"))
        await session.execute(text("DROP TABLE IF EXISTS phone_plans_db CASCADE"))
        
        # Create all tables
        async with session.begin():
            await session.run_sync(Base.metadata.create_all)
        
        print("Database tables recreated successfully!")

if __name__ == "__main__":
    asyncio.run(recreate_tables()) 