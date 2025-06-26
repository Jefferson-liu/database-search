from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import get_db
from backend.services.autosave_service import autosave_user_search
from backend.schemas.message import UserSearchCreate

router = APIRouter()

@router.post("/autosave/user")
async def autosave_user_search_hook(
    search: UserSearchCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await autosave_user_search(search.user_id, search.search_id, search, db)
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autosave failed: {str(e)}") 