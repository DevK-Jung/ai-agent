"""
문서 도메인 관련 의존성
"""
from functools import lru_cache
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.document_service import DocumentService
from app.services.document_processor import DocumentProcessor
from app.infra.storage.file_storage import FileStorageService
from .database import get_database_session
from .storage import get_file_storage_service
from .ai import get_embedding_service_cached


@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """DocumentProcessor 의존성 주입 (싱글톤)"""
    return DocumentProcessor()


def get_document_service(
    db: AsyncSession = Depends(get_database_session),
    file_storage: FileStorageService = Depends(get_file_storage_service),
    processor: DocumentProcessor = Depends(get_document_processor),
    embedding_service = Depends(get_embedding_service_cached)
) -> DocumentService:
    """DocumentService 의존성 주입"""
    return DocumentService(db, file_storage, processor, embedding_service)


__all__ = [
    "get_document_processor",
    "get_document_service"
]