import logging
from typing import List, Dict, Any, Optional

from app.core.config.settings import Settings
from .repository import SearchRepository
from .schemas import SearchRequest, VectorSearchRequest, SearchResponse, SearchResult

logger = logging.getLogger(__name__)


class SearchService:
    """검색 서비스 - 비즈니스 로직"""

    def __init__(self, repository: SearchRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def search_documents(self, request: SearchRequest) -> SearchResponse:
        """문서 텍스트 검색"""
        try:
            # 입력 검증
            if not request.query or len(request.query.strip()) == 0:
                return SearchResponse(
                    results=[],
                    total_count=0,
                    query=request.query,
                    collection_name=request.collection_name
                )

            # k 값 검증 및 제한
            k = min(max(request.k, 1), 100)  # 1~100 사이로 제한

            # 검색 수행
            results, processing_time = await self.repository.similarity_search(
                query=request.query,
                k=k,
                collection_name=request.collection_name,
                metadata_filter=request.metadata_filter,
                score_threshold=request.score_threshold
            )

            return SearchResponse(
                results=results,
                total_count=len(results),
                query=request.query,
                collection_name=request.collection_name,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return SearchResponse(
                results=[],
                total_count=0,
                query=request.query,
                collection_name=request.collection_name
            )

    async def search_by_vector(self, request: VectorSearchRequest) -> SearchResponse:
        """벡터로 문서 검색"""
        try:
            # 입력 검증
            if not request.embedding:
                return SearchResponse(
                    results=[],
                    total_count=0,
                    collection_name=request.collection_name
                )

            # k 값 검증 및 제한
            k = min(max(request.k, 1), 100)  # 1~100 사이로 제한

            # 벡터 검색 수행
            results, processing_time = await self.repository.vector_search(
                embedding=request.embedding,
                k=k,
                collection_name=request.collection_name,
                metadata_filter=request.metadata_filter,
                score_threshold=request.score_threshold
            )

            return SearchResponse(
                results=results,
                total_count=len(results),
                collection_name=request.collection_name,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return SearchResponse(
                results=[],
                total_count=0,
                collection_name=request.collection_name
            )

    async def search_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        collection_name: Optional[str] = None,
        limit: int = 100
    ) -> SearchResponse:
        """메타데이터로 문서 검색"""
        try:
            # 입력 검증
            if not metadata_filter:
                return SearchResponse(
                    results=[],
                    total_count=0,
                    collection_name=collection_name
                )

            # limit 값 검증 및 제한
            limit = min(max(limit, 1), 1000)  # 1~1000 사이로 제한

            # 메타데이터 검색 수행
            results, processing_time = await self.repository.metadata_search(
                metadata_filter=metadata_filter,
                collection_name=collection_name,
                limit=limit
            )

            return SearchResponse(
                results=results,
                total_count=len(results),
                collection_name=collection_name,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"메타데이터 검색 실패: {e}")
            return SearchResponse(
                results=[],
                total_count=0,
                collection_name=collection_name
            )

    async def hybrid_search(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, Any]] = None,
        k: int = 5,
        collection_name: Optional[str] = None,
        score_threshold: Optional[float] = None
    ) -> SearchResponse:
        """하이브리드 검색 (텍스트 + 메타데이터)"""
        try:
            # 기본적으로 텍스트 검색과 동일하지만 메타데이터 필터 적용
            request = SearchRequest(
                query=query,
                k=k,
                collection_name=collection_name,
                metadata_filter=metadata_filter,
                score_threshold=score_threshold
            )

            return await self.search_documents(request)

        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            return SearchResponse(
                results=[],
                total_count=0,
                query=query,
                collection_name=collection_name
            )