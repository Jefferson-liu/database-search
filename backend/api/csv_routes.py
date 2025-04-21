from fastapi import APIRouter, UploadFile, File, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from backend.services import csv_service, provider_name_service
from backend.db.session import get_db

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    row_count = await csv_service.store_csv_to_db(file, db)
    return {"message": f"Uploaded {row_count} rows."}

@router.get("/providers")
async def get_providers(db: AsyncSession = Depends(get_db)):
    return await provider_name_service.get_unique_providers(db)
