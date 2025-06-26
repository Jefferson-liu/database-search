from backend.models.sales_models import SalesSearchMessage, SalesUser, SalesUserRequirements, SalesUserSearch
from backend.schemas.user_requirements import UserRequirements
from backend.schemas.message import SearchMessageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_ , func
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from backend.services.search_query_service import get_search_results, extract_user_requirements
from backend.models.sales_models import SearchResults
import json
from collections import defaultdict

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
        prev_requirements = await get_user_requirements(payload.user_id, payload.search_id, db)
        new_requirements_dict = await extract_user_requirements(payload.content)
        merged_requirements = merge_requirements(prev_requirements, new_requirements_dict)
        response = await get_search_results(db=db, user_input=payload.content, requirements=merged_requirements)
        await set_user_requirements(payload.user_id, payload.search_id, merged_requirements, db)
        response_msg = SalesSearchMessage(
            user_id=user.id,
            search_id=payload.search_id,
            direction="outgoing",
            content=response.followup,
        )
        await save_message(response_msg, db)

        # Create search results record
        search_results = SearchResults(
            message_id=response_msg.id,
            user_id=user.id,
            search_id=payload.search_id,
            plans=json.loads(response.model_dump_json())["plans"],
            followup=response.followup
        )
        db.add(search_results)
        await db.flush()
        await db.commit()
        await db.refresh(search_results)

        return {
                "search_id": payload.search_id,
                "user_id": user.id,
                "incoming_message_id": message.id,
                "outgoing_message_id": response_msg.id,
                "results": json.loads(response.model_dump_json())
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

async def get_or_create_user(id: str, db: AsyncSession) -> SalesUser:
    """
    Get or create a sales user in the database.
    """
    result = await db.execute(select(SalesUser).where(SalesUser.id == id))
    user = result.scalar_one_or_none()
    if not user:
        user = SalesUser(
            id=id,
            name=f"User_{id}",  # Default name
            email=f"user_{id}@example.com"  # Default email
        )
        db.add(user)
        await db.flush()
        await db.commit()
        await db.refresh(user)
    return user

async def get_user_requirements(user_id: str, search_id: int, db: AsyncSession):
    """
    Get the user requirements for a given user ID and search ID.
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

async def set_user_requirements(user_id: str, search_id: int, req: UserRequirements, db: AsyncSession):
    """
    Upsert the user requirements for a given user ID and search ID.
    """
    result = await db.execute(
        select(SalesUserRequirements)
        .where(
            and_(
                SalesUserRequirements.user_id == user_id,
                SalesUserRequirements.search_id == search_id
            )
        )
    )
    requirements_row = result.scalar_one_or_none()
    if requirements_row is None:
        # Insert new requirements row
        requirements_row = SalesUserRequirements(
            user_id=user_id,
            search_id=search_id,
            current_provider=req.current_provider,
            target_price=req.target_price,
            target_data=req.target_data,
            min_data_gb=req.min_data_gb,
            byod=req.byod,
            roaming=req.roaming
        )
        db.add(requirements_row)
    else:
        # Update existing row
        for field in req.__class__.model_fields:
            value = getattr(req, field, None)
            if value is not None:
                setattr(requirements_row, field, value)
    await db.flush()
    await db.commit()
    await db.refresh(requirements_row)
    return requirements_row

async def get_user_messages(user_id: str, db: AsyncSession):
    """
    Get all messages for a given user ID.
    """
    stmt = (
        select(
            SalesSearchMessage,
            SalesUserSearch.customer_name,
            SearchResults.plans,
            SearchResults.message_id
        )
        .join(SalesUserSearch, SalesSearchMessage.search_id == SalesUserSearch.id)
        .outerjoin(SearchResults, SearchResults.message_id == SalesSearchMessage.id)
        .where(SalesSearchMessage.user_id == user_id)
    )

    result = await db.execute(stmt)
    rows = result.all()

    # Group everything by search_id
    grouped = defaultdict(lambda: {
        "customer_name": None,
        "messages": [],
        "plans": defaultdict(list)  # message_id → list of plans
    })

    for message, customer_name, plans, message_id in rows:
        entry = grouped[message.search_id]
        entry["customer_name"] = customer_name

        entry["messages"].append({
            "id": message.id,
            "direction": message.direction,
            "content": message.content,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        })

        if plans:
            entry["plans"][message.id].append(plans)

    # Convert plans dict to a list of {message_id, plans}
    final_output = []
    for sid, data in grouped.items():
        plans_list = [
            {"message_id": mid, "plans": plans}
            for mid, plans in data["plans"].items()
        ]
        final_output.append({
            "search_id": sid,
            "customer_name": data["customer_name"],
            "messages": data["messages"],
            "plans": plans_list
        })

    return final_output

def merge_requirements(existing: UserRequirements, new: dict) -> UserRequirements:
    # Start with previous requirements if they exist, otherwise empty
    if existing is not None:
        merged = existing.model_copy()
    else:
        merged = UserRequirements()
    # Update with any new values provided
    for field, value in new.items():
        if value is not None:
            setattr(merged, field, value)
    return merged
    