from backend.models.sales_models import SalesUserRequirements, SalesUserSearch
from backend.schemas.user_requirements import UserRequirements
from backend.schemas.message import UserSearchCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException

async def autosave_user_requirements(user_id: str, search_id: str, req: UserRequirements, db: AsyncSession):
    """
    Upsert (autosave) the user requirements for a given user ID and search ID, allowing partial data.
    """
    try:
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
            # Update existing row with any new values
            for field in req.__class__.model_fields:
                value = getattr(req, field, None)
                if value is not None:
                    setattr(requirements_row, field, value)
        await db.flush()
        await db.commit()
        await db.refresh(requirements_row)
        return {"status": "success", "search_id": search_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Autosave failed: {str(e)}")

async def autosave_user_search(user_id: str, search_id: str, search: UserSearchCreate, db: AsyncSession):
    """
    Upsert (autosave) the user search for a given user ID and search ID, allowing partial data (e.g., customer_name).
    """
    try:
        result = await db.execute(
            select(SalesUserSearch)
            .where(
                and_(
                    SalesUserSearch.user_id == user_id,
                    SalesUserSearch.id == search_id
                )
            )
        )
        search_row = result.scalar_one_or_none()
        if search_row is None:
            # Insert new search row
            search_row = SalesUserSearch(
                id=search_id,
                user_id=user_id,
                customer_name=search.customer_name
            )
            db.add(search_row)
        else:
            # Update existing row with any new values
            if search.customer_name is not None:
                search_row.customer_name = search.customer_name
        await db.flush()
        await db.commit()
        await db.refresh(search_row)
        return {"status": "success", "search_id": search_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Autosave failed: {str(e)}") 