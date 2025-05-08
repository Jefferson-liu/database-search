class UserRequirements:
    current_provider: str = None
    target_price: float = None
    target_data: float = None
    roaming: list = None
    min_data_gb: float = None
    byod: bool = None

    def __init__(self, current_provider=None, target_price=None, target_data=None, roaming=None, min_data_gb=None, byod=None):
        self.current_provider = current_provider
        self.target_price = target_price
        self.target_data = target_data
        self.roaming = roaming
        self.min_data_gb = min_data_gb
        self.byod = byod
    
    def to_dict(self):
        return {
            "current_provider": self.current_provider,
            "target_price": self.target_price,
            "target_data": self.target_data,
            "roaming": self.roaming,
            "min_data_gb": self.min_data_gb,
            "byod": self.byod
        }
    
    def from_dict(self, data):
        self.current_provider = data.get("current_provider")
        self.target_price = data.get("target_price")
        self.target_data = data.get("target_data")
        self.roaming = data.get("roaming")
        self.min_data_gb = data.get("min_data_gb")
        self.byod = data.get("byod")

    def __repr__(self):
        return f"UserRequirements(current_provider={self.current_provider}, target_price={self.target_price}, target_data={self.target_data}, roaming={self.roaming}, min_data_gb={self.min_data_gb}, byod={self.byod})"
    
    def missing_fields(self):
        missing = []
        if not self.current_provider:
            missing.append("current_provider")
        if not self.target_price:
            missing.append("target_price")
        if not self.target_data:
            missing.append("target_data")
        if not self.roaming:
            missing.append("roaming")
        if not self.min_data_gb:
            missing.append("min_data_gb")
        if not self.byod:
            missing.append("byod")
        return missing
    
    def get_current_provider(self):
        return self.current_provider
    
    def get_target_price(self):
        return self.target_price
    
    def get_target_data(self):
        return self.target_data
    
    def get_roaming(self):
        return self.roaming
    
    def get_min_data_gb(self):
        return self.min_data_gb
    
    def get_byod(self):
        return self.byod
    
    def set_current_provider(self, current_provider):
        self.current_provider = current_provider

    def set_target_price(self, target_price):
        self.target_price = target_price

    def set_target_data(self, target_data):
        self.target_data = target_data

    def set_roaming(self, roaming):
        self.roaming = roaming

    def set_min_data_gb(self, min_data_gb):
        self.min_data_gb = min_data_gb

    def set_byod(self, byod):
        self.byod = byod    
