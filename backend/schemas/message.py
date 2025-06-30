from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    openid: str #user id
    direction: str  # 'incoming' or 'outgoing'
    msg_type: Optional[str] = "text"
    content: Optional[str] = None
    msg_id: Optional[str] = None

class MessageOut(BaseModel):
    openid: str #user id
    content: str
    created_at: datetime

    class Config:
        orm_mode = True

class SearchMessageCreate(BaseModel):
    user_id: str
    search_id: str
    direction: Optional[str] = "incoming"  # 'incoming' or 'outgoing'
    content: Optional[str] = None

class UserSearchCreate(BaseModel):
    search_id: str
    user_id: str
    customer_name: Optional[str] = None