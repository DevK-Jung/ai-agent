from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid


class DocumentBase(BaseModel):
    title: str
    file_name: Optional[str] = None
    file_type: Optional[str] = None


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str
    chunk_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    id: uuid.UUID
    title: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    status: str
    message: str


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class DocumentChunkResponse(BaseModel):
    id: uuid.UUID
    chunk_index: int
    content: str
    token_count: Optional[int] = None
    char_count: Optional[int] = None
    chunk_type: str = "text"
    created_at: datetime

    class Config:
        from_attributes = True