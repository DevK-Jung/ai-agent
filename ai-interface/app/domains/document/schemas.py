from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.domains.document.constants import ChunkingStrategy


class DocumentInfo(BaseModel):
    """문서 정보"""
    document_id: str
    content: str
    metadata: Dict[str, Any] = {}
    collection_name: Optional[str] = None


class DocumentUploadRequest(BaseModel):
    """텍스트 문서 업로드 요청"""
    content: str
    filename: Optional[str] = None
    metadata: Dict[str, Any] = {}
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER


class FileUploadRequest(BaseModel):
    """파일 업로드 요청 (내부 처리용)"""
    file_content: bytes
    filename: str
    metadata: Dict[str, Any] = {}
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER


class DocumentUploadResponse(BaseModel):
    """문서 업로드 응답"""
    success: bool
    message: str
    document_ids: List[str]
    chunk_count: int
    total_tokens: Optional[int] = None


class DocumentUpdateRequest(BaseModel):
    """문서 업데이트 요청"""
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentDeleteResponse(BaseModel):
    """문서 삭제 응답"""
    success: bool
    message: str
    deleted_count: int
    deleted_ids: List[str] = []