# app/core/schemas/vector_schemas.py
from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator

from .constants import DocumentType, ChunkingStrategy, SearchType


# ========================================
# 요청/응답 스키마
# ========================================

class DocumentRequest(BaseModel):
    """문서 추가 요청"""
    content: str = Field(..., min_length=1, max_length=1000000, description="문서 내용")
    metadata: Optional[Dict[str, Any]] = Field(None, description="문서 메타데이터")
    document_type: DocumentType = Field(DocumentType.TEXT, description="문서 타입")
    chunk_size: Optional[int] = Field(None, ge=100, le=5000, description="청크 크기")
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000, description="청크 겹침")
    chunking_strategy: ChunkingStrategy = Field(ChunkingStrategy.RECURSIVE_CHARACTER, description="분할 전략")

    class Config:
        schema_extra = {
            "example": {
                "content": "이것은 샘플 문서입니다. LangChain과 PGVector를 사용한 벡터 검색 시스템입니다.",
                "metadata": {
                    "title": "벡터 검색 가이드",
                    "author": "개발팀",
                    "category": "기술문서",
                    "tags": ["AI", "벡터검색", "LangChain"]
                },
                "document_type": "text",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "chunking_strategy": "recursive_character"
            }
        }


class DocumentResponse(BaseModel):
    """문서 추가 응답"""
    document_id: str = Field(..., description="문서 고유 ID")
    chunks_count: int = Field(..., ge=1, description="생성된 청크 수")
    message: str = Field(..., description="처리 결과 메시지")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 정보")

    class Config:
        schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunks_count": 3,
                "message": "문서가 성공적으로 3개 청크로 저장되었습니다",
                "metadata": {
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "chunking_strategy": "recursive_character",
                    "collection_name": "documents",
                    "vector_ids": ["vec_001", "vec_002", "vec_003"]
                }
            }
        }


class SearchRequest(BaseModel):
    """검색 요청"""
    query: str = Field(..., min_length=1, max_length=1000, description="검색 쿼리")
    k: Optional[int] = Field(5, ge=1, le=100, description="반환할 결과 수")
    collection_name: Optional[str] = Field(None, description="검색할 컬렉션 이름")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="메타데이터 필터")
    score_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="최소 유사도 점수")
    search_type: SearchType = Field(SearchType.SIMILARITY, description="검색 타입")

    class Config:
        schema_extra = {
            "example": {
                "query": "벡터 검색 시스템",
                "k": 5,
                "collection_name": "tech_docs",
                "metadata_filter": {
                    "$and": [
                        {"category": {"$eq": "기술문서"}},
                        {"tags": {"$in": ["AI", "벡터검색"]}}
                    ]
                },
                "score_threshold": 0.3,
                "search_type": "similarity"
            }
        }


class SearchResult(BaseModel):
    """검색 결과 항목"""
    content: str = Field(..., description="문서 내용")
    metadata: Dict[str, Any] = Field(..., description="문서 메타데이터")
    score: float = Field(..., description="유사도 점수 (낮을수록 유사)")
    document_id: Optional[str] = Field(None, description="문서 ID")
    chunk_id: Optional[str] = Field(None, description="청크 ID")

    class Config:
        schema_extra = {
            "example": {
                "content": "벡터 검색 시스템은 문서의 의미를 벡터로 변환하여 유사한 문서를 찾는 기술입니다.",
                "metadata": {
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "title": "벡터 검색 가이드",
                    "category": "기술문서",
                    "chunk_index": 0,
                    "created_at": 1640995200
                },
                "score": 0.234,
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunk_id": "550e8400-e29b-41d4-a716-446655440000_0"
            }
        }


class SearchResponse(BaseModel):
    """검색 응답"""
    query: str = Field(..., description="검색 쿼리")
    results: List[SearchResult] = Field(..., description="검색 결과 목록")
    total_results: int = Field(..., ge=0, description="총 결과 수")
    execution_time_ms: float = Field(..., ge=0, description="실행 시간 (밀리초)")
    collection_name: Optional[str] = Field(None, description="검색된 컬렉션")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="적용된 필터")

    class Config:
        schema_extra = {
            "example": {
                "query": "벡터 검색 시스템",
                "results": [
                    {
                        "content": "벡터 검색 시스템은 문서의 의미를 벡터로 변환하여 유사한 문서를 찾는 기술입니다.",
                        "metadata": {"title": "벡터 검색 가이드", "category": "기술문서"},
                        "score": 0.234,
                        "document_id": "550e8400-e29b-41d4-a716-446655440000"
                    }
                ],
                "total_results": 1,
                "execution_time_ms": 45.67,
                "collection_name": "tech_docs"
            }
        }


# ========================================
# 상태 관련 스키마
# ========================================

class VectorStoreStatus(BaseModel):
    """벡터 저장소 상태"""
    is_connected: bool = Field(..., description="연결 상태")
    collection_count: int = Field(..., ge=0, description="컬렉션 수")
    total_documents: int = Field(..., ge=0, description="총 문서 수")
    embedding_model: str = Field(..., description="사용 중인 임베딩 모델")
    status_message: str = Field(..., description="상태 메시지")
    embedding_dimension: Optional[int] = Field(None, description="임베딩 차원")
    pgvector_version: Optional[str] = Field(None, description="PGVector 버전")

    class Config:
        schema_extra = {
            "example": {
                "is_connected": True,
                "collection_count": 3,
                "total_documents": 1250,
                "embedding_model": "nomic-embed-text",
                "status_message": "정상 작동 중",
                "embedding_dimension": 768,
                "pgvector_version": "0.5.1"
            }
        }


class ConnectionTest(BaseModel):
    """연결 테스트 결과"""
    service: str = Field(..., description="서비스 이름")
    status: bool = Field(..., description="연결 상태")
    response_time_ms: Optional[float] = Field(None, description="응답 시간 (밀리초)")
    version: Optional[str] = Field(None, description="서비스 버전")
    error_message: Optional[str] = Field(None, description="오류 메시지")


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(..., description="전체 상태 (healthy/unhealthy)")
    timestamp: datetime = Field(..., description="체크 시간")
    services: List[ConnectionTest] = Field(..., description="서비스별 상태")
    recommendations: List[str] = Field(default_factory=list, description="권장사항")

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "services": [
                    {
                        "service": "postgresql",
                        "status": True,
                        "response_time_ms": 12.34,
                        "version": "16.1"
                    },
                    {
                        "service": "ollama",
                        "status": True,
                        "response_time_ms": 45.67,
                        "version": "0.1.26"
                    }
                ],
                "recommendations": ["모든 연결이 정상입니다!"]
            }
        }


# ========================================
# 컬렉션 관련 스키마
# ========================================

class CollectionInfo(BaseModel):
    """컬렉션 정보"""
    name: str = Field(..., description="컬렉션 이름")
    document_count: int = Field(..., ge=0, description="문서 수")
    created_at: Optional[datetime] = Field(None, description="생성 시간")
    last_updated: Optional[datetime] = Field(None, description="마지막 업데이트")
    size_bytes: Optional[int] = Field(None, description="크기 (바이트)")


class CollectionStats(BaseModel):
    """컬렉션 통계"""
    collection_name: str = Field(..., description="컬렉션 이름")
    total_documents: int = Field(..., ge=0, description="총 문서 수")
    total_chunks: int = Field(..., ge=0, description="총 청크 수")
    unique_metadata_fields: List[str] = Field(default_factory=list, description="고유 메타데이터 필드")
    document_types: Dict[str, int] = Field(default_factory=dict, description="문서 타입별 개수")
    size_info: Dict[str, Any] = Field(default_factory=dict, description="크기 정보")
    oldest_document: Optional[datetime] = Field(None, description="가장 오래된 문서")
    newest_document: Optional[datetime] = Field(None, description="가장 최신 문서")

    class Config:
        schema_extra = {
            "example": {
                "collection_name": "tech_docs",
                "total_documents": 150,
                "total_chunks": 450,
                "unique_metadata_fields": ["title", "author", "category", "tags"],
                "document_types": {"text": 100, "pdf": 30, "markdown": 20},
                "size_info": {
                    "total_size_mb": 25.6,
                    "avg_document_size_kb": 175.3
                },
                "oldest_document": "2024-01-01T00:00:00Z",
                "newest_document": "2024-01-15T10:30:00Z"
            }
        }


# ========================================
# 배치 작업 스키마
# ========================================

class BatchDocumentRequest(BaseModel):
    """배치 문서 추가 요청"""
    documents: List[DocumentRequest] = Field(..., min_items=1, max_items=100, description="문서 목록")
    collection_name: Optional[str] = Field(None, description="컬렉션 이름")
    batch_size: Optional[int] = Field(10, ge=1, le=50, description="배치 크기")


class BatchDocumentResponse(BaseModel):
    """배치 문서 추가 응답"""
    total_documents: int = Field(..., description="총 처리된 문서 수")
    successful_documents: int = Field(..., description="성공한 문서 수")
    failed_documents: int = Field(..., description="실패한 문서 수")
    document_ids: List[str] = Field(..., description="생성된 문서 ID 목록")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="오류 목록")
    processing_time_ms: float = Field(..., description="총 처리 시간")


class BulkDeleteRequest(BaseModel):
    """대량 삭제 요청"""
    document_ids: Optional[List[str]] = Field(None, description="삭제할 문서 ID 목록")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="메타데이터 필터")
    collection_name: Optional[str] = Field(None, description="컬렉션 이름")
    confirm_delete: bool = Field(False, description="삭제 확인 (안전장치)")

    @validator('confirm_delete')
    def validate_delete_confirmation(cls, v, values):
        """삭제 확인 검증"""
        if not v:
            raise ValueError("대량 삭제 작업은 confirm_delete=True로 설정해야 합니다")
        return v

    @validator('metadata_filter')
    def validate_delete_filter(cls, v, values):
        """삭제 필터 검증"""
        if v is None and values.get('document_ids') is None:
            raise ValueError("document_ids 또는 metadata_filter 중 하나는 필수입니다")
        return v


class BulkDeleteResponse(BaseModel):
    """대량 삭제 응답"""
    deleted_count: int = Field(..., ge=0, description="삭제된 문서 수")
    deleted_document_ids: List[str] = Field(default_factory=list, description="삭제된 문서 ID 목록")
    processing_time_ms: float = Field(..., description="처리 시간")
    collection_name: Optional[str] = Field(None, description="컬렉션 이름")


# ========================================
# 파일 업로드 스키마
# ========================================

class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""
    filename: str = Field(..., description="업로드된 파일명")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    file_type: str = Field(..., description="파일 타입")
    document_response: DocumentResponse = Field(..., description="문서 처리 결과")

    class Config:
        schema_extra = {
            "example": {
                "filename": "technical_guide.pdf",
                "file_size": 2048576,
                "file_type": "pdf",
                "document_response": {
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "chunks_count": 5,
                    "message": "파일이 성공적으로 5개 청크로 저장되었습니다"
                }
            }
        }


# ========================================
# 에러 응답 스키마
# ========================================

class VectorErrorResponse(BaseModel):
    """벡터 도메인 에러 응답"""
    error_code: str = Field(..., description="에러 코드")
    error_message: str = Field(..., description="에러 메시지")
    error_type: str = Field(..., description="에러 타입")
    details: Optional[Dict[str, Any]] = Field(None, description="상세 정보")
    timestamp: datetime = Field(default_factory=datetime.now, description="에러 발생 시간")

    class Config:
        schema_extra = {
            "example": {
                "error_code": "VECTOR_001",
                "error_message": "문서 저장 중 오류가 발생했습니다",
                "error_type": "VectorStoreError",
                "details": {
                    "collection_name": "tech_docs",
                    "document_count": 5
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
