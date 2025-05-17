from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.schemas.message import MessageCreate
from backend.db.session import get_db
from backend.services.wechat_service import process_message, get_wechat_history

router = APIRouter()

@router.post("/wechat/message")
async def receive_wechat_message(payload: MessageCreate, db: AsyncSession = Depends(get_db)):
    try:
        message = await process_message(payload, db)
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store message: {str(e)}")


@router.get("/wechat/{openid}/messages")
async def get_message_history(openid: str, db: AsyncSession = Depends(get_db)):
    try:
        messages = await get_wechat_history(openid, db)
        return messages
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve message history: {str(e)}")
