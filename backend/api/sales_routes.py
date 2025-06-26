from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.services.search_query_service import get_search_results
from backend.services.search_message_service import process_message, get_user_messages
from backend.schemas.message import SearchMessageCreate
from backend.services.autosave_service import autosave_user_requirements
from backend.schemas.user_requirements import UserRequirements

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

@router.get("/messages/")
async def get_messages(user_id: str, db: AsyncSession = Depends(get_db)):
    try:
        messages = await get_user_messages(user_id, db)
        return messages
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/message/")
async def receive_message(content: SearchMessageCreate, db: AsyncSession = Depends(get_db)):
    try:
        message = await process_message(content, db)
        return message
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")