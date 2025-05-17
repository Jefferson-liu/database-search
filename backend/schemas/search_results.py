from typing import List, Optional
from datetime import date
from pydantic import BaseModel

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
    byod_or_term: Optional[bool]
    free_ld: Optional[str]
    activation_fee: Optional[float]
    promo_start_date: Optional[date]
    promo_end_date: Optional[date]
    code: Optional[str]
    tier: Optional[str]

class SearchResults(BaseModel):
    plans: List[PlanInfo]
    followup: Optional[str] = None
