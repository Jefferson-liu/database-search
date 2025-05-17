from backend.models.sales_models import SalesSearchMessage, SalesUser, SalesUserRequirements
from backend.schemas.user_requirements import UserRequirements
from backend.schemas.message import SearchMessageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from backend.services.search_query_service import get_search_results

async def process_message(payload: SearchMessageCreate, db: AsyncSession) -> dict:
    try:
        user = await get_or_create_user(payload.user_id, db)
        message = SalesSearchMessage(
            search_id=payload.search_id,
            user_id=user.id,
            direction="incoming",
            content=payload.content,
        )
        await save_message(message, db)
        messages = await get_user_requirements(payload.user_id, db)
        response = await get_search_results(db= db, user_input=payload.content, prev_requirements=messages)
        response_msg = SalesSearchMessage(
            user_id=user.id,
            search_id=payload.search_id,
            direction="outgoing",
            content=response["followup"],
        )
        await save_message(response_msg, db)
        return {
                "search_id": payload.search_id,
                "user_id": user.id,
                "incoming_message_id": message.id,
                "outgoing_message_id": response_msg.id,
                "results": response.model_dump()
            }

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Database error: " + str(e.orig))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def save_message(message: SalesSearchMessage, db: AsyncSession):
    """
    Save the message to the database.
    """
    db.add(message)
    await db.flush()
    await db.commit()
    await db.refresh(message)
    return message

async def get_or_create_user(openid: str, db: AsyncSession) -> SalesUser:
    """
    Get or create a sales user in the database.
    """
    result = await db.execute(select(SalesUser).where(SalesUser.openid == openid))
    user = result.scalar_one_or_none()
    if not user:
        user = SalesUser(openid=openid)
        db.add(user)
        await db.flush()
        await db.commit()
        await db.refresh(user)
    return user

async def get_user_requirements(user_id: str, search_id: int, db: AsyncSession):
    """
    Get the search history of a user.
    """
    result = await db.execute(select(SalesUser).where(SalesUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.execute(
        select(SalesUserRequirements)
        .where(and_(SalesUserRequirements.user_id == user.id, SalesUserRequirements.search_id == search_id))
    )
    orm_row = result.scalar_one_or_none()
    if orm_row:
        user_requirements = UserRequirements(
            current_provider=orm_row.current_provider,
            target_price=orm_row.target_price,
            target_data=orm_row.target_data,
            min_data_gb=orm_row.min_data_gb,
            byod=orm_row.byod,
            roaming=orm_row.roaming
        )
    else:
        return None
    return user_requirements