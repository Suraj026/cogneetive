from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)

class QueryResponse(BaseModel):
    results: List[str]

class ErrorResponse(BaseModel):
    error: str
    detail: str

class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "unknown"
    sources: List[str] = []
    degree: int = 0

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    sources: List[str] = []

class GraphDataResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: dict