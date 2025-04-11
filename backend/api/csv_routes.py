from fastapi import APIRouter, UploadFile, File, Query
from backend.services import csv_service, search_service
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    df = await csv_service.store_csv(file)
    return {"message": "CSV uploaded", "rows": len(df)}

@router.get("/search")
def search_csv(query: str = Query(...)):
    df = csv_service.get_dataframe()
    if df is None:
        return JSONResponse(status_code=404, content={"error": "No CSV uploaded"})
    results = search_service.search_csv(df, query)
    return results
