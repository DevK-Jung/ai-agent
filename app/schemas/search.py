"""
검색 관련 스키마
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid


class SearchRequest(BaseModel):
    """검색 요청 스키마"""
    query: str = Field(..., description="검색할 질의", min_length=1)
    limit: int = Field(default=10, description="반환할 최대 결과 수", ge=1, le=50)
    threshold: float = Field(default=0.5, description="유사도 임계값", ge=0.0, le=1.0)
    filters: Optional[Dict[str, Any]] = Field(default=None, description="추가 필터링 옵션")


class SearchResult(BaseModel):
    """개별 검색 결과 스키마"""
    chunk_id: uuid.UUID = Field(..., description="청크 ID")
    document_id: uuid.UUID = Field(..., description="문서 ID") 
    document_title: str = Field(..., description="문서 제목")
    file_name: Optional[str] = Field(None, description="파일명")
    content: str = Field(..., description="청크 내용")
    similarity_score: float = Field(..., description="유사도 점수", ge=0.0, le=1.0)
    chunk_index: int = Field(..., description="문서 내 청크 순서")
    chunk_type: str = Field(default="text", description="청크 유형")
    token_count: Optional[int] = Field(None, description="토큰 수")
    char_count: Optional[int] = Field(None, description="문자 수")
    page_number: Optional[int] = Field(None, description="페이지 번호")
    created_at: datetime = Field(..., description="생성 시간")


class SearchResponse(BaseModel):
    """검색 응답 스키마"""
    query: str = Field(..., description="검색 질의")
    results: List[SearchResult] = Field(..., description="검색 결과 목록")
    total_results: int = Field(..., description="총 결과 수")
    search_time: float = Field(..., description="검색 소요 시간 (초)")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="적용된 필터")
    
    
class SearchStats(BaseModel):
    """검색 통계 스키마"""
    total_documents: int = Field(..., description="총 문서 수")
    total_chunks: int = Field(..., description="총 청크 수")
    embedding_model: str = Field(..., description="사용된 임베딩 모델")
    embedding_dimensions: int = Field(..., description="임베딩 차원 수")