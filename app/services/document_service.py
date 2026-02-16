import uuid
from typing import List, Optional, Tuple
from fastapi import UploadFile

import logging
from app.models.document import Document, DocumentChunk
from app.repositories.document_repository import DocumentRepository
from app.infra.storage.file_storage import FileStorageService
from app.services.document_processor import DocumentProcessor
from app.infra.ai.embedding_service import get_embedding_service
from app.core.config import settings


class DocumentService:
    """문서 관리 서비스 - Repository 패턴 적용"""
    
    def __init__(
        self, 
        document_repository: DocumentRepository,
        file_storage: FileStorageService = None,
        processor: DocumentProcessor = None,
        embedding_service = None
    ):
        self.document_repository = document_repository
        self.logger = logging.getLogger(__name__)
        self.file_storage = file_storage or FileStorageService()
        self.processor = processor or DocumentProcessor()
        self.embedding_service = embedding_service or get_embedding_service()
    
    async def create_document_from_upload(self, file: UploadFile) -> Document:
        """
        업로드된 파일로부터 Document 레코드를 생성합니다.
        
        Args:
            file: 업로드된 파일
            
        Returns:
            Document: 생성된 문서 객체
        """
        try:
            # 문서 ID 생성
            document_id = uuid.uuid4()
            
            # 파일 저장
            upload_result = await self.file_storage.save_uploaded_file(file, document_id)
            
            # 파일에서 텍스트 추출
            content = self.processor.extract_text_from_file(upload_result.file_path, file.content_type)
            
            # 텍스트 유효성 검증
            if not self.processor.validate_file_content(content):
                raise ValueError("파일에서 유효한 텍스트를 추출할 수 없습니다.")
            
            # Document 객체 생성 (content는 저장하지 않음)
            document = Document(
                id=document_id,
                title=file.filename or f"Document_{document_id}",
                file_name=file.filename,
                file_path=upload_result.file_path,
                file_size=upload_result.file_size,
                file_type=file.content_type,
                content_hash=upload_result.content_hash,
                language="ko",  # 기본값
                status="pending"
            )
            
            # 데이터베이스 저장 (Repository에 위임)
            document = await self.document_repository.create_document(document)
            
            self.logger.info(f"문서 생성 완료: {document_id}")
            return document
            
        except Exception as e:
            self.logger.error(f"문서 생성 실패: {e}")
            raise
    
    async def process_document_async(self, document_id: uuid.UUID):
        """
        문서를 비동기적으로 처리합니다 (청킹 + 임베딩).
        백그라운드 태스크로 실행됩니다.
        
        Args:
            document_id: 처리할 문서 ID
        """
        try:
            # 문서 조회 (Repository에 위임)
            document = await self.document_repository.get_document_by_id(document_id)
            if not document:
                raise ValueError(f"문서를 찾을 수 없습니다: {document_id}")
            
            # 상태를 processing으로 변경 (Repository에 위임)
            document.status = "processing"
            await self.document_repository.update_document(document)
            
            self.logger.info(f"문서 처리 시작: {document_id}")
            
            # 파일에서 텍스트 추출
            if not document.file_path:
                raise ValueError("파일 경로가 없습니다.")
            
            content = self.processor.extract_text_from_file(document.file_path, document.file_type)
            
            # 텍스트 청킹
            chunks_data = self.processor.chunk_text(
                content,
                metadata={"document_id": str(document_id), "file_name": document.file_name}
            )
            
            if not chunks_data:
                raise ValueError("텍스트에서 청크를 생성할 수 없습니다.")
            
            # 청크별 임베딩 생성 및 저장
            chunk_contents = [chunk["content"] for chunk in chunks_data]
            embeddings = self.embedding_service.batch_encode(chunk_contents, batch_size=16)
            
            chunk_objects = []
            for chunk_data, embedding in zip(chunks_data, embeddings):
                if embedding is not None:  # 임베딩 생성 성공한 경우만
                    chunk = DocumentChunk(
                        id=uuid.uuid4(),
                        document_id=document_id,
                        chunk_index=chunk_data["chunk_index"],
                        content=chunk_data["content"],
                        content_hash=chunk_data["content_hash"],
                        embedding=embedding.tolist(),  # numpy array를 list로 변환
                        embedding_model=settings.EMBEDDING_MODEL,
                        token_count=chunk_data["token_count"],
                        char_count=chunk_data["char_count"],
                        start_position=chunk_data["start_position"],
                        end_position=chunk_data["end_position"],
                        chunk_type=chunk_data["chunk_type"],
                        extra_metadata=chunk_data["extra_metadata"]
                    )
                    chunk_objects.append(chunk)
            
            # 청크들을 데이터베이스에 저장 (Repository에 위임)
            if chunk_objects:
                await self.document_repository.create_chunks(chunk_objects)
            
            # 문서 상태 업데이트 (Repository에 위임)
            document.chunk_count = len(chunk_objects)
            document.status = "completed" if chunk_objects else "failed"
            await self.document_repository.update_document(document)
            
            self.logger.info(f"문서 처리 완료: {document_id}, 청크 수: {len(chunk_objects)}")
            
        except Exception as e:
            # 실패 시 상태 업데이트
            try:
                document = await self.document_repository.get_document_by_id(document_id)
                if document:
                    document.status = "failed"
                    await self.document_repository.update_document(document)
            except:
                pass
            
            self.logger.error(f"문서 처리 실패: {document_id}, 오류: {e}")
            raise
    
    async def get_document_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """
        문서 ID로 문서를 조회합니다.
        
        Args:
            document_id: 문서 ID
            
        Returns:
            Document: 문서 객체 또는 None
        """
        # Repository에 위임
        return await self.document_repository.get_document_by_id(document_id)
    
    async def get_documents(
        self, 
        skip: int = 0, 
        limit: int = 20, 
        status: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        """
        문서 목록을 조회합니다.
        
        Args:
            skip: 건너뛸 개수
            limit: 가져올 최대 개수
            status: 필터링할 상태
            
        Returns:
            Tuple[List[Document], int]: (문서 목록, 전체 개수)
        """
        # Repository에 위임
        try:
            documents = await self.document_repository.find_documents(skip, limit, status)
            total = await self.document_repository.count_documents(status)
            return documents, total
        except Exception as e:
            self.logger.error(f"문서 목록 조회 실패: {e}")
            return [], 0
    
    async def delete_document(self, document_id: uuid.UUID) -> bool:
        """
        문서를 삭제합니다 (파일 및 모든 청크 포함).
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            # 문서 조회 (Repository에 위임)
            document = await self.document_repository.get_document_by_id(document_id)
            if not document:
                return False
            
            # 파일 삭제
            if document.file_path:
                self.file_storage.delete_file(document.file_path)
            
            # 데이터베이스에서 삭제 (Repository에 위임)
            success = await self.document_repository.delete_document(document_id)
            
            if success:
                self.logger.info(f"문서 삭제 완료: {document_id}")
            return success
            
        except Exception as e:
            self.logger.error(f"문서 삭제 실패: {e}")
            return False
    
    async def search_similar_chunks(
        self, 
        query_embedding: List[float], 
        limit: int = 10,
        threshold: float = 0.5
    ) -> List[DocumentChunk]:
        """
        임베딩을 사용하여 유사한 청크를 검색합니다.
        
        Args:
            query_embedding: 질의 임베딩 벡터
            limit: 반환할 최대 개수
            threshold: 유사도 임계값
            
        Returns:
            List[DocumentChunk]: 유사한 청크 리스트
        """
        # Repository에 위임
        return await self.document_repository.find_similar_chunks(query_embedding, limit, threshold)