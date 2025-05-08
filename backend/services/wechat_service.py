from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from backend.models.wechat_models import WeChatUser, WeChatMessage
from backend.schemas.query import QueryRequest
from backend.schemas.message import MessageCreate
from backend.services.query_service import query_model

async def process_message(payload: MessageCreate, db: AsyncSession) -> dict:
    try:
        user = await get_or_create_user(payload.openid, db)
        message = WeChatMessage(
            user_id=user.id,
            direction=payload.direction,
            msg_type=payload.msg_type,
            content=payload.content,
            msg_id=payload.msg_id
        )
        await save_message(message, db)
        messages = await get_wechat_history(payload.openid, db)
        response = await generate_response_message(payload.content, db, messages)
        response_msg = WeChatMessage(
            user_id=user.id,
            direction="outgoing",
            msg_type=payload.msg_type,
            content=response["answer"],
            msg_id=payload.msg_id
        )
        await save_message(response_msg, db)
        return response

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error: " + str(e.orig))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def get_wechat_history(openid: str, db: AsyncSession):
    result = await db.execute(select(WeChatUser).where(WeChatUser.openid == openid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(WeChatMessage)
        .where(WeChatMessage.user_id == user.id)
        .order_by(WeChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "role": "system", "content": "You are a helpful business assistant. Do not answer anything unless it can be backed up with retrieved knowledge or structured data. If unsure, say 'I don't know based on the available data.' Do not make assumptions, do not hallucinate. Respond in the language you are asked in. Meet all customer requirements with every response. If you cannot, meet as many as you can. If you cannot meet any, say 'I don't know based on the available data.'",
            "role": "user" if m.direction == "incoming" else "assistant",
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "msg_id": m.msg_id,
        }
        for m in messages if m.content
    ]

async def get_or_create_user(openid: str, db: AsyncSession) -> WeChatUser:
    result = await db.execute(select(WeChatUser).where(WeChatUser.openid == openid))
    user = result.scalar_one_or_none()
    if not user:
        user = WeChatUser(openid=openid)
        db.add(user)
        await db.flush()
    return user

async def save_message(message, db: AsyncSession) -> WeChatMessage:
    db.add(message)
    await db.flush()
    await db.commit()
    await db.refresh(message)
    return message

async def generate_response_message(content: str, db: AsyncSession, history) -> WeChatMessage:
    req = QueryRequest(question=content)
    response = await query_model(db, req, message_history=history)
    return response
