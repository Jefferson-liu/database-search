from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.services.query_service import query_model
from backend.schemas.query import QueryRequest
router = APIRouter()

@router.post("/query")
async def query_phone_plans(req: QueryRequest, db: AsyncSession = Depends(get_db)):
    try:
        response = await query_model(db, req)
    except HTTPException as he:
        raise he 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response
