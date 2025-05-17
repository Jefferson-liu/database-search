from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.base import Base
from sqlalchemy.orm import relationship

class SalesUser(Base):
    __tablename__ = "sales_users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # optional: or use email/username if preferred
    email = Column(String, unique=True, nullable=False)

    # Backref to access messages
    messages = relationship("SalesSearchMessage", back_populates="user", cascade="all, delete-orphan")
    requirements = relationship("SalesUserRequirements", back_populates="user", cascade="all, delete-orphan")


class SalesSearchMessage(Base):
    __tablename__ = "sales_search_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sales_users.id", ondelete="CASCADE"), nullable=False)
    search_id = Column(String, nullable=False, index=True)  # New: groups messages in one logical search session
    direction = Column(String, nullable=False)  # "incoming" or "outgoing"
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("SalesUser", back_populates="messages")

class SalesUserRequirements(Base):
    __tablename__ = "sales_user_requirements"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("sales_users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("SalesUser", back_populates="requirements")

    # New: groups together related requirements in one logical search session
    search_id = Column(String, nullable=False, index=True)

    current_provider = Column(String, nullable=True)
    target_price = Column(Float, nullable=True)
    target_data = Column(Float, nullable=True)
    min_data_gb = Column(Float, nullable=True)
    byod = Column(Boolean, nullable=True)
    
    # Recommended: use JSONB if using Postgres
    from sqlalchemy.dialects.postgresql import JSONB
    roaming = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
