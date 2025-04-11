from fastapi import APIRouter, UploadFile, File, Depends, Request
from sqlalchemy.orm import Session
from backend.services import csv_service, search_service, provider_name_service
from backend.db.session import get_db

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    row_count = await csv_service.store_csv_to_db(file, db)
    return {"message": f"Uploaded {row_count} rows."}

@router.get("/search")
def search_csv(request: Request, db: Session = Depends(get_db)):
    filters = dict(request.query_params)
    return search_service.search_csv(db, filters)

@router.get("/providers")
def get_providers(db: Session = Depends(get_db)):
    return provider_name_service.get_unique_providers(db)
