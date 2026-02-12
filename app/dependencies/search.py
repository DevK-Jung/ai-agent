"""
검색 관련 의존성
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.search_service import SearchService
from app.dependencies.database import get_database_session
from app.dependencies.ai import get_embedding_service_cached


def get_search_service(
    db: AsyncSession = Depends(get_database_session),
    embedding_service = Depends(get_embedding_service_cached)
) -> SearchService:
    """SearchService 의존성 주입"""
    return SearchService(db, embedding_service)


__all__ = ["get_search_service"]