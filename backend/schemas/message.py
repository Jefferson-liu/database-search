from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageCreate(BaseModel):
    openid: str
    direction: str  # 'incoming' or 'outgoing'
    msg_type: Optional[str] = "text"
    content: Optional[str] = None
    msg_id: Optional[str] = None

class MessageOut(BaseModel):
    id: int
    direction: str
    msg_type: str
    content: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
