import logging
import time
from typing import List, Optional, Dict, Any

from app.infra.vector_db.client import VectorDBClient
from .schemas import SearchResult

logger = logging.getLogger(__name__)


class SearchRepository:
    """검색 리포지토리 - 저수준 검색 액세스"""

    def __init__(self, vector_db_client: VectorDBClient):
        self.vector_db_client = vector_db_client

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> tuple[List[SearchResult], int]:
        """텍스트 유사도 검색"""
        try:
            start_time = time.time()
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            # 검색 수행
            if score_threshold:
                docs_with_scores = await vectorstore.asimilarity_search_with_relevance_scores(
                    query=query,
                    k=k,
                    filter=metadata_filter,
                    score_threshold=score_threshold
                )
                docs = [(doc, score) for doc, score in docs_with_scores]
            else:
                docs_and_scores = await vectorstore.asimilarity_search_with_score(
                    query=query,
                    k=k,
                    filter=metadata_filter
                )
                docs = docs_and_scores

            # 결과 변환
            results = []
            for doc, score in docs:
                result = SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=float(score) if score is not None else None,
                    document_id=doc.metadata.get("document_id")
                )
                results.append(result)

            processing_time = int((time.time() - start_time) * 1000)

            return results, processing_time

        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            return [], 0

    async def vector_search(
        self,
        embedding: List[float],
        k: int = 5,
        collection_name: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        score_threshold: Optional[float] = None
    ) -> tuple[List[SearchResult], int]:
        """벡터 검색"""
        try:
            start_time = time.time()
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            # 벡터 검색 수행
            if score_threshold:
                docs_with_scores = await vectorstore.asimilarity_search_by_vector_with_relevance_scores(
                    embedding=embedding,
                    k=k,
                    filter=metadata_filter,
                    score_threshold=score_threshold
                )
                docs = [(doc, score) for doc, score in docs_with_scores]
            else:
                docs = await vectorstore.asimilarity_search_by_vector(
                    embedding=embedding,
                    k=k,
                    filter=metadata_filter
                )
                # 점수 없는 경우 None으로 설정
                docs = [(doc, None) for doc in docs]

            # 결과 변환
            results = []
            for doc, score in docs:
                result = SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=float(score) if score is not None else None,
                    document_id=doc.metadata.get("document_id")
                )
                results.append(result)

            processing_time = int((time.time() - start_time) * 1000)

            return results, processing_time

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return [], 0

    async def metadata_search(
        self,
        metadata_filter: Dict[str, Any],
        collection_name: Optional[str] = None,
        limit: int = 100
    ) -> tuple[List[SearchResult], int]:
        """메타데이터 검색"""
        try:
            start_time = time.time()
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            # 빈 쿼리로 메타데이터 필터만 사용하여 검색
            docs = await vectorstore.asimilarity_search(
                query="",
                k=limit,
                filter=metadata_filter
            )

            # 결과 변환
            results = []
            for doc in docs:
                result = SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=None,  # 메타데이터 검색에서는 점수 없음
                    document_id=doc.metadata.get("document_id")
                )
                results.append(result)

            processing_time = int((time.time() - start_time) * 1000)

            return results, processing_time

        except Exception as e:
            logger.error(f"메타데이터 검색 실패: {e}")
            return [], 0