"""Pydantic models for API requests and responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for querying documents."""
    query: str
    top_k: Optional[int] = None
    threshold: Optional[float] = None


class SourceItem(BaseModel):
    """Model for a single source item."""
    chunk: str
    similarity: float
    metadata: Dict[str, Any]


class QueryResponse(BaseModel):
    """Response model for query results."""
    answer: str
    sources: List[SourceItem]
    query: str


class IngestRequest(BaseModel):
    """Request model for ingesting documents."""
    file_path: Optional[str] = None
    text: Optional[str] = None


class IngestResponse(BaseModel):
    """Response model for ingestion results."""
    message: str
    chunks_added: int
    total_chunks: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    vector_store_stats: Dict[str, Any]
