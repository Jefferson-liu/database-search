from sqlalchemy import Column, Integer, Float, String, DateTime, Date
from backend.db.base import Base
from pgvector.sqlalchemy import Vector

class CsvRow(Base):
    __tablename__ = "phone_plans_db"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String)
    item_name = Column(String)
    provider = Column(String)
    promo_start_date = Column(Date)
    promo_end_date = Column(Date)
    channel = Column(String)
    region = Column(String)
    condition = Column(String)
    line_type = Column(Float)
    promotion_price = Column(Float)
    data = Column(Float)
    original_price = Column(Float)
    overage_rate = Column(Float)
    roaming = Column(String)
    byod_or_term = Column(Float)
    free_ld = Column(String)
    activation_fee = Column(Float)
    code = Column(String)
    tier = Column(String)
    embedding = Column(Vector(384))
