from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON, ForeignKey, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from sqlalchemy.orm import relationship
import uuid

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # Fallback for development without pgvector installed
    from sqlalchemy import Text as Vector

from app.db.database import Base
from app.core.config import settings


class Document(Base):
    """Document 마스터 테이블 - 원본 문서 정보"""
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=True)
    file_path = Column(String(1000), nullable=True)
    file_size = Column(Integer, nullable=True)  # bytes
    file_type = Column(String(50), nullable=True)  # pdf, txt, docx, etc
    # content는 저장하지 않고, 필요시 file_path에서 읽어옴
    content_hash = Column(String(64), nullable=True)  # SHA256 해시 (중복 체크용)
    source_url = Column(String(1000), nullable=True)  # 웹에서 수집된 경우 원본 URL
    language = Column(String(10), nullable=True, default='ko')  # 언어 코드
    total_tokens = Column(Integer, nullable=True)  # 총 토큰 수
    chunk_count = Column(Integer, nullable=True, default=0)  # 생성된 청크 수
    status = Column(String(20), nullable=False, default='pending')  # pending, processing, completed, failed
    extra_metadata = Column(JSON, nullable=True)  # 추가 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        # 기존 단일 인덱스
        Index('ix_documents_status', 'status'),
        Index('ix_documents_created_at', 'created_at'),
        Index('ix_documents_content_hash', 'content_hash'),
        
        # Phase 1: 핵심 복합 인덱스 - 가장 빈번한 쿼리 패턴 최적화
        Index('ix_documents_status_created_at', 'status', 'created_at'),  # status + 날짜 정렬 조합
        Index('ix_documents_file_type_status', 'file_type', 'status'),   # 파일타입 필터링 + 상태 확인
        
        # 부분 인덱스: 완료된 문서만 대상 (90% 쿼리가 completed 조회)
        Index('ix_documents_completed_created_at', 'created_at', 
              postgresql_where=text("status = 'completed'")),
    )


class DocumentChunk(Base):
    """Document 청크 테이블 - 분할된 텍스트와 임베딩"""
    __tablename__ = "document_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # 문서 내에서의 청크 순서
    content = Column(Text, nullable=False)  # 청크 텍스트 내용
    content_hash = Column(String(64), nullable=True)  # 청크 내용의 해시
    
    # Embedding 관련
    embedding = Column(Vector(settings.EMBEDDING_DIMENSIONS), nullable=True)  # 환경변수에서 차원 설정
    embedding_model = Column(String(50), nullable=True, default=settings.EMBEDDING_MODEL)
    
    # 텍스트 처리 정보
    token_count = Column(Integer, nullable=True)  # 청크의 토큰 수
    char_count = Column(Integer, nullable=True)  # 청크의 문자 수
    
    # 청크 위치 정보 (원본 문서에서의 위치)
    start_position = Column(Integer, nullable=True)  # 원본에서 시작 위치
    end_position = Column(Integer, nullable=True)  # 원본에서 끝 위치
    
    # 청크 유형 및 메타데이터
    chunk_type = Column(String(20), nullable=False, default='text')  # text, title, header, etc
    section_title = Column(String(200), nullable=True)  # 속한 섹션 제목
    page_number = Column(Integer, nullable=True)  # PDF 등에서 페이지 번호
    
    extra_metadata = Column(JSON, nullable=True)  # 추가 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        # 기존 인덱스
        Index('ix_document_chunks_document_id', 'document_id'),
        Index('ix_document_chunks_chunk_index', 'document_id', 'chunk_index'),
        # 기본 벡터 인덱스 - IVFFlat (호환성) todo 제거 hnsw만 사용
        Index('ix_document_chunks_embedding_ivf', 'embedding', postgresql_using='ivfflat', postgresql_ops={'embedding': 'vector_cosine_ops'}),
        
        # Phase 3: HNSW 인덱스 - 더 나은 성능 (pgvector 0.5.0+)
        Index('ix_document_chunks_embedding_hnsw', 'embedding', postgresql_using='hnsw', postgresql_ops={'embedding': 'vector_cosine_ops'}),
        
        # Phase 2: JOIN 최적화 - Document 테이블과의 조인 성능 향상
        Index('ix_document_chunks_join_optimized', 'document_id', 'chunk_type', 'chunk_index'),  # covering index for frequent joins
        
        # 청크 타입 필터링 최적화
        Index('ix_document_chunks_chunk_type', 'chunk_type'),
        
        # 텍스트 검색 최적화 (content 길이 기반 부분 인덱스)
        Index('ix_document_chunks_content_length', 'char_count', 
              postgresql_where=text("char_count > 50")),  # 너무 짧은 청크 제외
        
        # 임베딩이 있는 청크만 대상 (벡터 검색용)
        Index('ix_document_chunks_with_embedding', 'document_id', 'embedding_model',
              postgresql_where=text("embedding IS NOT NULL")),
    )