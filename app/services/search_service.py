"""
검색 서비스
"""
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from app.models.document import Document, DocumentChunk
from app.infra.ai.embedding_service import get_embedding_service
from app.schemas.search import SearchRequest, SearchResult, SearchResponse, SearchStats
from app.core.config import settings


class SearchService:
    """임베딩 기반 검색 서비스"""
    
    def __init__(self, db: AsyncSession, embedding_service=None):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.embedding_service = embedding_service or get_embedding_service()
    
    async def semantic_search(self, search_request: SearchRequest) -> SearchResponse:
        """
        의미적 검색을 수행합니다.
        
        Args:
            search_request: 검색 요청 정보
            
        Returns:
            SearchResponse: 검색 결과
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"의미 검색 시작: '{search_request.query}'")
            
            # 1. 질의 텍스트를 임베딩으로 변환
            query_embedding = self.embedding_service.get_embeddings(search_request.query)
            
            # 2. 벡터 유사도 검색 수행
            chunks = await self._vector_search(
                query_embedding=query_embedding.tolist(),
                limit=search_request.limit,
                threshold=search_request.threshold,
                filters=search_request.filters
            )
            
            # 3. 검색 결과를 응답 형식으로 변환
            search_results = await self._format_search_results(chunks, query_embedding)
            
            search_time = time.time() - start_time
            
            self.logger.info(f"의미 검색 완료: {len(search_results)}개 결과, {search_time:.3f}초")
            
            return SearchResponse(
                query=search_request.query,
                results=search_results,
                total_results=len(search_results),
                search_time=search_time,
                filters_applied=search_request.filters
            )
            
        except Exception as e:
            self.logger.error(f"의미 검색 실패: {e}")
            raise
    
    async def _vector_search(
        self,
        query_embedding: List[float],
        limit: int,
        threshold: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        벡터 유사도 검색을 수행합니다.
        
        Args:
            query_embedding: 질의 임베딩
            limit: 결과 개수 제한
            threshold: 유사도 임계값
            filters: 추가 필터
            
        Returns:
            List[DocumentChunk]: 검색된 청크들
        """
        try:
            # 기본 쿼리: 코사인 유사도 검색
            stmt = select(DocumentChunk).join(Document).where(
                # 유사도 임계값 적용
                DocumentChunk.embedding.cosine_distance(query_embedding) < (1 - threshold),
                # 완료된 문서의 청크만 검색
                Document.status == "completed"
            ).options(
                joinedload(DocumentChunk.document)
            ).order_by(
                DocumentChunk.embedding.cosine_distance(query_embedding)
            ).limit(limit)
            
            # 추가 필터 적용
            if filters:
                conditions = []
                
                # 문서 타입 필터
                if "file_types" in filters and filters["file_types"]:
                    conditions.append(Document.file_type.in_(filters["file_types"]))
                
                # 문서 ID 필터
                if "document_ids" in filters and filters["document_ids"]:
                    conditions.append(Document.id.in_(filters["document_ids"]))
                
                # 청크 타입 필터
                if "chunk_types" in filters and filters["chunk_types"]:
                    conditions.append(DocumentChunk.chunk_type.in_(filters["chunk_types"]))
                
                # 날짜 범위 필터
                if "date_from" in filters and filters["date_from"]:
                    conditions.append(Document.created_at >= filters["date_from"])
                
                if "date_to" in filters and filters["date_to"]:
                    conditions.append(Document.created_at <= filters["date_to"])
                
                if conditions:
                    stmt = stmt.where(and_(*conditions))
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"벡터 검색 실패: {e}")
            raise
    
    async def _format_search_results(
        self, 
        chunks: List[DocumentChunk], 
        query_embedding
    ) -> List[SearchResult]:
        """
        검색 결과를 응답 형식으로 변환합니다.
        
        Args:
            chunks: 검색된 청크들
            query_embedding: 질의 임베딩 (유사도 계산용)
            
        Returns:
            List[SearchResult]: 변환된 검색 결과
        """
        search_results = []
        
        for chunk in chunks:
            # 유사도 점수 계산 (1 - 코사인 거리)
            similarity_score = 1 - float(
                chunk.embedding.cosine_distance(query_embedding.tolist()) 
                if hasattr(chunk.embedding, 'cosine_distance') 
                else self.embedding_service.compute_similarity(
                    query_embedding, chunk.embedding
                )
            )
            
            search_result = SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_title=chunk.document.title,
                file_name=chunk.document.file_name,
                content=chunk.content,
                similarity_score=max(0.0, min(1.0, similarity_score)),  # 0-1 범위로 제한
                chunk_index=chunk.chunk_index,
                chunk_type=chunk.chunk_type,
                token_count=chunk.token_count,
                char_count=chunk.char_count,
                page_number=chunk.page_number,
                created_at=chunk.created_at
            )
            
            search_results.append(search_result)
        
        return search_results
    
    async def get_search_stats(self) -> SearchStats:
        """
        검색 시스템 통계를 반환합니다.
        
        Returns:
            SearchStats: 검색 시스템 통계
        """
        try:
            # 총 문서 수
            doc_count_stmt = select(func.count(Document.id)).where(
                Document.status == "completed"
            )
            doc_result = await self.db.execute(doc_count_stmt)
            total_documents = doc_result.scalar()
            
            # 총 청크 수
            chunk_count_stmt = select(func.count(DocumentChunk.id))
            chunk_result = await self.db.execute(chunk_count_stmt)
            total_chunks = chunk_result.scalar()
            
            return SearchStats(
                total_documents=total_documents,
                total_chunks=total_chunks,
                embedding_model=settings.EMBEDDING_MODEL,
                embedding_dimensions=settings.EMBEDDING_DIMENSIONS
            )
            
        except Exception as e:
            self.logger.error(f"검색 통계 조회 실패: {e}")
            raise
    
    async def hybrid_search(
        self,
        search_request: SearchRequest,
        keyword_weight: float = 0.3,
        semantic_weight: float = 0.7
    ) -> SearchResponse:
        """
        하이브리드 검색 (키워드 + 의미적 검색)을 수행합니다.
        
        Args:
            search_request: 검색 요청
            keyword_weight: 키워드 검색 가중치
            semantic_weight: 의미적 검색 가중치
            
        Returns:
            SearchResponse: 검색 결과
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"하이브리드 검색 시작: '{search_request.query}'")
            
            # 1. 의미적 검색
            semantic_results = await self.semantic_search(search_request)
            
            # 2. 키워드 검색 (간단한 전문 검색)
            keyword_chunks = await self._keyword_search(
                query=search_request.query,
                limit=search_request.limit,
                filters=search_request.filters
            )
            
            # 3. 점수 결합 및 재랭킹
            combined_results = self._combine_search_results(
                semantic_results.results,
                keyword_chunks,
                semantic_weight,
                keyword_weight
            )
            
            search_time = time.time() - start_time
            
            self.logger.info(f"하이브리드 검색 완료: {len(combined_results)}개 결과, {search_time:.3f}초")
            
            return SearchResponse(
                query=search_request.query,
                results=combined_results[:search_request.limit],
                total_results=len(combined_results),
                search_time=search_time,
                filters_applied=search_request.filters
            )
            
        except Exception as e:
            self.logger.error(f"하이브리드 검색 실패: {e}")
            raise
    
    async def _keyword_search(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        키워드 기반 전문 검색을 수행합니다.
        
        Args:
            query: 검색 질의
            limit: 결과 개수 제한
            filters: 추가 필터
            
        Returns:
            List[DocumentChunk]: 검색된 청크들
        """
        try:
            # PostgreSQL 전문 검색 (단순 ILIKE 사용)
            stmt = select(DocumentChunk).join(Document).where(
                DocumentChunk.content.ilike(f"%{query}%"),
                Document.status == "completed"
            ).options(
                joinedload(DocumentChunk.document)
            ).order_by(
                DocumentChunk.chunk_index
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"키워드 검색 실패: {e}")
            return []
    
    def _combine_search_results(
        self,
        semantic_results: List[SearchResult],
        keyword_chunks: List[DocumentChunk],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[SearchResult]:
        """
        의미적 검색과 키워드 검색 결과를 결합합니다.
        
        Args:
            semantic_results: 의미적 검색 결과
            keyword_chunks: 키워드 검색 청크
            semantic_weight: 의미적 검색 가중치
            keyword_weight: 키워드 검색 가중치
            
        Returns:
            List[SearchResult]: 결합된 검색 결과
        """
        # 청크 ID별로 점수 집계
        score_map = {}
        result_map = {}
        
        # 의미적 검색 결과 추가
        for result in semantic_results:
            chunk_id = result.chunk_id
            score_map[chunk_id] = result.similarity_score * semantic_weight
            result_map[chunk_id] = result
        
        # 키워드 검색 결과 추가 (간단한 점수 계산)
        for chunk in keyword_chunks:
            chunk_id = chunk.id
            keyword_score = 0.8  # 키워드 매칭에 대한 기본 점수
            
            if chunk_id in score_map:
                # 이미 있으면 점수 결합
                score_map[chunk_id] += keyword_score * keyword_weight
            else:
                # 새로운 결과면 추가
                score_map[chunk_id] = keyword_score * keyword_weight
                result_map[chunk_id] = SearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_title=chunk.document.title,
                    file_name=chunk.document.file_name,
                    content=chunk.content,
                    similarity_score=keyword_score,
                    chunk_index=chunk.chunk_index,
                    chunk_type=chunk.chunk_type,
                    token_count=chunk.token_count,
                    char_count=chunk.char_count,
                    page_number=chunk.page_number,
                    created_at=chunk.created_at
                )
        
        # 최종 점수로 정렬
        sorted_results = []
        for chunk_id, combined_score in sorted(score_map.items(), key=lambda x: x[1], reverse=True):
            result = result_map[chunk_id]
            result.similarity_score = min(1.0, combined_score)  # 최대값 1.0으로 제한
            sorted_results.append(result)
        
        return sorted_results