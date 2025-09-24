from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class SearchResult(BaseModel):
    """검색 결과 항목"""
    content: str
    metadata: Dict[str, Any] = {}
    score: Optional[float] = None
    document_id: Optional[str] = None


class SearchRequest(BaseModel):
    """텍스트 검색 요청"""
    query: str
    k: int = 5
    collection_name: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = None


class VectorSearchRequest(BaseModel):
    """벡터 검색 요청"""
    embedding: List[float]
    k: int = 5
    collection_name: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    score_threshold: Optional[float] = None


class SearchResponse(BaseModel):
    """검색 응답"""
    results: List[SearchResult]
    total_count: int
    query: Optional[str] = None
    collection_name: Optional[str] = None
    processing_time_ms: Optional[int] = None