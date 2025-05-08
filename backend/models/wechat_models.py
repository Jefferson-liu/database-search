from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, CheckConstraint, UniqueConstraint, func, Index
from sqlalchemy.orm import relationship
from backend.db.base import Base

class WeChatUser(Base):
    __tablename__ = "wechat_users"

    id = Column(Integer, primary_key=True, index=True)
    openid = Column(String, unique=True, nullable=False)  # WeChat user ID
    nickname = Column(String)
    last_seen = Column(TIMESTAMP, server_default=func.now())

    messages = relationship("WeChatMessage", back_populates="user", lazy="selectin")
    class Config:
        orm_mode = True


class WeChatMessage(Base):
    __tablename__ = "wechat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("wechat_users.id"), nullable=False)
    direction = Column(String, nullable=False)  # 'incoming' or 'outgoing'
    msg_type = Column(String)  # e.g. 'text', 'image', 'event'
    content = Column(Text)
    msg_id = Column(String)  # optional, from WeChat
    created_at = Column(TIMESTAMP, server_default=func.now())
    

    user = relationship("WeChatUser", back_populates="messages")

    __table_args__ = (
        CheckConstraint("direction IN ('incoming', 'outgoing')", name="check_direction_valid"),
        Index("idx_user_created_at", "user_id", "created_at")

    )
    class Config:
        orm_mode = True
