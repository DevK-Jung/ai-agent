"""
검색 관련 의존성
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search_service import SearchService
from app.repositories.search_repository import SearchRepository
from app.dependencies.database import get_database_session
from app.dependencies.ai import get_embedding_service


def get_search_repository(
    db: AsyncSession = Depends(get_database_session)
) -> SearchRepository:
    """SearchRepository 의존성 주입"""
    return SearchRepository(db)


def get_search_service(
    search_repository: SearchRepository = Depends(get_search_repository),
    embedding_service = Depends(get_embedding_service)
) -> SearchService:
    """SearchService 의존성 주입 - Repository 패턴 적용"""
    return SearchService(search_repository, embedding_service)


__all__ = ["get_search_service", "get_search_repository"]