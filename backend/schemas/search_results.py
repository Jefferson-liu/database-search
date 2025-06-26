from typing import List, Optional
from datetime import date
from pydantic import BaseModel, field_validator

class PlanInfo(BaseModel):
    item_name: Optional[str]
    provider: Optional[str]
    region: Optional[str]
    condition: Optional[str]
    channel: Optional[str]
    line_type: Optional[float]
    promotion_price: Optional[float]
    original_price: Optional[float]
    overage_rate: Optional[float]
    data: Optional[float]
    roaming: Optional[List[str]]
    byod_or_term: Optional[float]
    free_ld: Optional[str]
    activation_fee: Optional[float]
    promo_start_date: Optional[date]
    promo_end_date: Optional[date]
    code: Optional[str]
    tier: Optional[str]

    @field_validator('byod_or_term')
    @classmethod
    def convert_byod_to_bool(cls, v: Optional[float]) -> Optional[bool]:
        if v is None:
            return None
        return v == 1.0

class SearchResults(BaseModel):
    plans: List[PlanInfo]
    followup: Optional[str] = None
