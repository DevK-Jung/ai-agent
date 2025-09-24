from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class CollectionInfo(BaseModel):
    """컬렉션 정보"""
    name: str = Field(..., description="collection 명")
    document_count: Optional[int] = Field(..., description="문서 수")
    metadata: Dict[str, Any] = Field({}, description="collection metadata")
    created_at: Optional[str] = None


class CollectionCreateRequest(BaseModel):
    """컬렉션 생성 요청"""
    name: str = Field(...,
                      min_length=1,
                      max_length=100,
                      description="collection 명")


class CollectionListResponse(BaseModel):
    """컬렉션 목록 응답"""
    collections: List[CollectionInfo]
    total_count: int


class CollectionResponse(BaseModel):
    """컬렉션 삭제 응답"""
    success: bool
    message: str
    collection_name: str
