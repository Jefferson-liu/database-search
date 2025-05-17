from typing import Optional, List
from pydantic import BaseModel

class UserRequirements(BaseModel):
    current_provider: Optional[str] = None
    target_price: Optional[float] = None
    target_data: Optional[float] = None
    roaming: Optional[List[str]] = None
    min_data_gb: Optional[float] = None
    byod: Optional[bool] = None


    def get_missing_fields(self) -> List[str]:
        return [field for field, value in self.model_dump().items() if value is None]

    def is_valid(self) -> bool:
        """
        Validate numerical fields for non-negative values.
        """
        if self.target_price is not None and self.target_price < 0:
            return False
        if self.target_data is not None and self.target_data < 0:
            return False
        if self.min_data_gb is not None and self.min_data_gb < 0:
            return False
        return True
