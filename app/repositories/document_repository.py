"""
문서 Repository

문서 및 청크 관련 데이터 액세스 로직
"""
import uuid
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete
from sqlalchemy.orm import selectinload, joinedload

from app.models.document import Document, DocumentChunk


class DocumentRepository:
    """문서 관련 데이터 액세스 클래스"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    async def create_document(self, document: Document) -> Document:
        """
        새 문서를 생성합니다.
        
        Args:
            document: 생성할 문서 객체
            
        Returns:
            Document: 생성된 문서 객체
        """
        try:
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)
            
            self.logger.debug(f"문서 생성 완료: {document.id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"문서 생성 실패: {e}")
            raise
    
    async def get_document_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """
        문서 ID로 문서를 조회합니다.
        
        Args:
            document_id: 문서 ID
            
        Returns:
            Document: 문서 객체 또는 None
        """
        try:
            stmt = select(Document).where(Document.id == document_id)
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"문서 조회 실패: {e}")
            return None
    
    async def get_document_with_chunks(self, document_id: uuid.UUID) -> Optional[Document]:
        """
        문서와 해당 청크들을 함께 조회합니다.
        
        Args:
            document_id: 문서 ID
            
        Returns:
            Document: 청크가 포함된 문서 객체 또는 None
        """
        try:
            stmt = select(Document).where(Document.id == document_id).options(
                selectinload(Document.chunks)
            )
            result = await self.db.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            self.logger.error(f"문서(청크 포함) 조회 실패: {e}")
            return None
    
    async def find_documents(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        status: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> List[Document]:
        """
        조건에 따른 문서 목록을 조회합니다.
        
        Args:
            skip: 건너뛸 개수
            limit: 가져올 최대 개수
            status: 필터링할 상태
            file_type: 필터링할 파일 타입
            
        Returns:
            List[Document]: 문서 목록
        """
        try:
            conditions = []
            if status:
                conditions.append(Document.status == status)
            if file_type:
                conditions.append(Document.file_type == file_type)
            
            stmt = select(Document)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(Document.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.db.execute(stmt)
            documents = result.scalars().all()
            
            self.logger.debug(f"문서 목록 조회 완료: {len(documents)}개")
            return list(documents)
            
        except Exception as e:
            self.logger.error(f"문서 목록 조회 실패: {e}")
            return []
    
    async def count_documents(
        self, 
        status: Optional[str] = None, 
        file_type: Optional[str] = None
    ) -> int:
        """
        조건에 따른 문서 개수를 조회합니다.
        
        Args:
            status: 필터링할 상태
            file_type: 필터링할 파일 타입
            
        Returns:
            int: 문서 개수
        """
        try:
            conditions = []
            if status:
                conditions.append(Document.status == status)
            if file_type:
                conditions.append(Document.file_type == file_type)
            
            stmt = select(func.count(Document.id))
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            result = await self.db.execute(stmt)
            count = result.scalar() or 0
            
            self.logger.debug(f"문서 개수 조회 완료: {count}개")
            return count
            
        except Exception as e:
            self.logger.error(f"문서 개수 조회 실패: {e}")
            return 0
    
    async def update_document(self, document: Document) -> Document:
        """
        문서 정보를 업데이트합니다.
        
        Args:
            document: 업데이트할 문서 객체
            
        Returns:
            Document: 업데이트된 문서 객체
        """
        try:
            await self.db.commit()
            await self.db.refresh(document)
            
            self.logger.debug(f"문서 업데이트 완료: {document.id}")
            return document
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"문서 업데이트 실패: {e}")
            raise
    
    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """
        문서를 삭제합니다.
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 문서 조회
            document = await self.get_document_by_id(document_id)
            if not document:
                return False
            
            # 문서 삭제 (CASCADE로 청크도 자동 삭제)
            await self.db.delete(document)
            await self.db.commit()
            
            self.logger.info(f"문서 삭제 완료: {document_id}")
            return True
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"문서 삭제 실패: {e}")
            return False
    
    async def create_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        문서 청크들을 생성합니다.
        
        Args:
            chunks: 생성할 청크 리스트
            
        Returns:
            List[DocumentChunk]: 생성된 청크 리스트
        """
        try:
            if chunks:
                self.db.add_all(chunks)
                await self.db.commit()
                
                # 모든 청크를 refresh
                for chunk in chunks:
                    await self.db.refresh(chunk)
            
            self.logger.debug(f"청크 생성 완료: {len(chunks)}개")
            return chunks
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"청크 생성 실패: {e}")
            raise
    
    async def find_chunks_by_document(
        self, 
        document_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        특정 문서의 청크들을 조회합니다.
        
        Args:
            document_id: 문서 ID
            limit: 최대 개수
            
        Returns:
            List[DocumentChunk]: 청크 리스트
        """
        try:
            stmt = select(DocumentChunk).where(
                DocumentChunk.document_id == document_id
            ).order_by(DocumentChunk.chunk_index)
            
            if limit:
                stmt = stmt.limit(limit)
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            self.logger.debug(f"문서 청크 조회 완료: {len(chunks)}개")
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"문서 청크 조회 실패: {e}")
            return []
    
    async def find_similar_chunks(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        threshold: float = 0.5,
        document_ids: Optional[List[uuid.UUID]] = None
    ) -> List[DocumentChunk]:
        """
        임베딩을 사용하여 유사한 청크를 검색합니다.
        
        Args:
            query_embedding: 질의 임베딩 벡터
            limit: 반환할 최대 개수
            threshold: 유사도 임계값
            document_ids: 검색 대상 문서 ID 목록 (선택사항)
            
        Returns:
            List[DocumentChunk]: 유사한 청크 리스트
        """
        try:
            conditions = [
                DocumentChunk.embedding.cosine_distance(query_embedding) < (1 - threshold)
            ]
            
            if document_ids:
                conditions.append(DocumentChunk.document_id.in_(document_ids))
            
            stmt = select(DocumentChunk).where(
                and_(*conditions)
            ).options(
                joinedload(DocumentChunk.document)
            ).order_by(
                DocumentChunk.embedding.cosine_distance(query_embedding)
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
            
            self.logger.debug(f"유사 청크 검색 완료: {len(chunks)}개")
            return list(chunks)
            
        except Exception as e:
            self.logger.error(f"유사 청크 검색 실패: {e}")
            return []
    
    async def get_documents_by_status(self, status: str) -> List[Document]:
        """
        특정 상태의 문서들을 조회합니다.
        
        Args:
            status: 문서 상태
            
        Returns:
            List[Document]: 해당 상태의 문서 리스트
        """
        try:
            stmt = select(Document).where(Document.status == status)
            result = await self.db.execute(stmt)
            documents = result.scalars().all()
            
            self.logger.debug(f"상태별 문서 조회 완료 ({status}): {len(documents)}개")
            return list(documents)
            
        except Exception as e:
            self.logger.error(f"상태별 문서 조회 실패: {e}")
            return []