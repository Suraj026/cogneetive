from pydantic import BaseModel, Field
from typing import List

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)

class QueryResponse(BaseModel):
    results: List[str]

class ErrorResponse(BaseModel):
    error: str
    detail: str