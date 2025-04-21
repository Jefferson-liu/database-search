from pydantic import BaseModel
class QueryRequest(BaseModel):
    question: str
    k: int = 1