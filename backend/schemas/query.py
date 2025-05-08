from pydantic import BaseModel
class QueryRequest(BaseModel):
    question: str = "I use rogers and am going on vacation to china"
    k: int = 3