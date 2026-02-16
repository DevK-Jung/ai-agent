"""
검색 Repository

벡터 검색, 키워드 검색 등 검색 관련 데이터 액세스 로직
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import joinedload

from app.models.document import Document, DocumentChunk


class SearchRepository:
    """검색 관련 데이터 액세스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def find_similar_chunks(
        self,
        query_embedding: List[float],
        limit: int,
        threshold: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        벡터 유사도 기반 청크 검색
        
        Args:
            query_embedding: 질의 임베딩 벡터
            limit: 결과 개수 제한
            threshold: 유사도 임계값
            filters: 추가 필터 조건
            
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
            
            # 필터 적용
            if filters:
                stmt = self._apply_filters(stmt, filters)
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            self.logger.debug(f"벡터 검색 완료: {len(chunks)}개 청크")
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"벡터 검색 실패: {e}")
            raise
    
    async def find_chunks_by_keyword(
        self,
        query: str,
        limit: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        키워드 기반 청크 검색
        
        Args:
            query: 검색 키워드
            limit: 결과 개수 제한
            filters: 추가 필터 조건
            
        Returns:
            List[DocumentChunk]: 검색된 청크들
        """
        try:
            # PostgreSQL 전문 검색 (ILIKE 사용)
            stmt = select(DocumentChunk).join(Document).where(
                DocumentChunk.content.ilike(f"%{query}%"),
                Document.status == "completed"
            ).options(
                joinedload(DocumentChunk.document)
            ).order_by(
                DocumentChunk.chunk_index
            ).limit(limit)
            
            # 필터 적용
            if filters:
                stmt = self._apply_filters(stmt, filters)
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            self.logger.debug(f"키워드 검색 완료: {len(chunks)}개 청크")
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"키워드 검색 실패: {e}")
            return []
    
    async def get_search_statistics(self) -> Dict[str, int]:
        """
        검색 시스템 통계 조회
        
        Returns:
            Dict[str, int]: 통계 정보
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
            
            # 임베딩이 있는 청크 수
            embedding_count_stmt = select(func.count(DocumentChunk.id)).where(
                DocumentChunk.embedding.isnot(None)
            )
            embedding_result = await self.db.execute(embedding_count_stmt)
            chunks_with_embedding = embedding_result.scalar()
            
            return {
                'total_documents': total_documents or 0,
                'total_chunks': total_chunks or 0,
                'chunks_with_embedding': chunks_with_embedding or 0
            }
            
        except Exception as e:
            self.logger.error(f"통계 조회 실패: {e}")
            raise
    
    async def find_chunks_with_filters(
        self,
        filters: Dict[str, Any],
        limit: int,
        offset: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        필터 조건에 따른 청크 검색
        
        Args:
            filters: 필터 조건
            limit: 결과 개수 제한
            offset: 오프셋
            
        Returns:
            List[DocumentChunk]: 검색된 청크들
        """
        try:
            stmt = select(DocumentChunk).join(Document).where(
                Document.status == "completed"
            ).options(
                joinedload(DocumentChunk.document)
            )
            
            # 필터 적용
            stmt = self._apply_filters(stmt, filters)
            
            # 페이징
            if offset:
                stmt = stmt.offset(offset)
            stmt = stmt.limit(limit)
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"필터 검색 실패: {e}")
            raise
    
    def _apply_filters(self, stmt, filters: Dict[str, Any]):
        """
        쿼리에 필터 조건 적용
        
        Args:
            stmt: SQLAlchemy 쿼리 문
            filters: 필터 조건들
            
        Returns:
            적용된 쿼리 문
        """
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
        
        # 조건 적용
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        return stmt