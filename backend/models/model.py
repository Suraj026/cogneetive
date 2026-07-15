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

class IngestionTriggerRequest(BaseModel):
    source: str = Field(..., min_length=1, description="Source type (e.g. 'slack', ''github')")
    channels: list[str] = Field(..., min_length=1, description="Channel names (e.g. ['#general', '#design'])")

class ChannelResult(BaseModel):
    status: str = Field(..., description="ok | skipped | not_found | failed | error")
    channel_id: str | None = None
    channel_name: str | None = None
    messages_count: int = 0
    error: str | None = None

class IngestionStatusResponse(BaseModel):
    id: str
    status: str = Field(..., description="running | completed | failed")
    channels: dict[str, ChannelResult] = {}
    error: str | None = None

class IngestionSourcesResponse(BaseModel):
    sources: list[str]