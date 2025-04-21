from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.csv_row import CsvRow

async def get_unique_providers(db: AsyncSession):
    result = await db.execute(select(CsvRow.provider).distinct())
    return {"providers" : result.scalars().all()}
