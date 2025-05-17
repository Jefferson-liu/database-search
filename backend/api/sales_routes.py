from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.services.search_query_service import get_search_results
router = APIRouter()

@router.post("/query")
async def query_phone_plans(user_input: str, db: AsyncSession = Depends(get_db)):
    try:
        response = await get_search_results(db, user_input)
    except HTTPException as he:
        raise he 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return response