from sqlalchemy import Column, Integer, Float, String, DateTime, Date
from sqlalchemy.dialects.postgresql import ARRAY
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
    roaming = Column(ARRAY(String))
    byod_or_term = Column(Float)
    free_ld = Column(String)
    activation_fee = Column(Float)
    code = Column(String)
    tier = Column(String)
    embedding = Column(Vector(384))

    def to_dict(self, include_embedding: bool = False) -> dict:
        d = {
            "id": self.id,
            "timestamp": self.timestamp,
            "item_name": self.item_name,
            "provider": self.provider,
            "promo_start_date": self.promo_start_date.isoformat() if self.promo_start_date else None,
            "promo_end_date": self.promo_end_date.isoformat() if self.promo_end_date else None,
            "channel": self.channel,
            "region": self.region,
            "condition": self.condition,
            "line_type": self.line_type,
            "promotion_price": self.promotion_price,
            "data": self.data,
            "original_price": self.original_price,
            "overage_rate": self.overage_rate,
            "roaming": self.roaming,
            "byod_or_term": self.byod_or_term,
            "free_ld": self.free_ld,
            "activation_fee": self.activation_fee,
            "code": self.code,
            "tier": self.tier,
        }
        if include_embedding:
            d["embedding"] = list(self.embedding) if self.embedding is not None else None
        return d
