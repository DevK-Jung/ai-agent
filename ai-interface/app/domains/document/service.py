import logging
from typing import List, Optional, Dict, Any

from app.core.config.settings import Settings
from .repository import DocumentRepository
from .schemas import (
    DocumentInfo,
    DocumentUploadRequest,
    DocumentUploadResponse,
    FileUploadRequest,
    DocumentUpdateRequest,
    DocumentDeleteResponse
)

logger = logging.getLogger(__name__)


class DocumentService:
    """문서 서비스 - 비즈니스 로직"""

    def __init__(self, repository: DocumentRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    async def upload_text_document(
        self,
        request: DocumentUploadRequest,
        collection_name: Optional[str] = None
    ) -> DocumentUploadResponse:
        """텍스트 문서 업로드"""
        try:
            # 입력 검증
            if not request.content or len(request.content.strip()) == 0:
                return DocumentUploadResponse(
                    success=False,
                    message="문서 내용이 비어있습니다",
                    document_ids=[],
                    chunk_count=0
                )

            # 텍스트 처리 및 청킹
            documents = self.repository.process_text_content(
                content=request.content,
                filename=request.filename,
                metadata=request.metadata,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                chunking_strategy=request.chunking_strategy
            )

            # 벡터 저장소에 추가
            document_ids = await self.repository.add_documents(documents, collection_name)

            return DocumentUploadResponse(
                success=True,
                message=f"{len(documents)}개의 청크로 분할되어 업로드되었습니다",
                document_ids=document_ids,
                chunk_count=len(documents)
            )

        except Exception as e:
            logger.error(f"텍스트 문서 업로드 실패: {e}")
            return DocumentUploadResponse(
                success=False,
                message=f"문서 업로드 중 오류가 발생했습니다: {str(e)}",
                document_ids=[],
                chunk_count=0
            )

    async def upload_file_document(
        self,
        request: FileUploadRequest,
        collection_name: Optional[str] = None
    ) -> DocumentUploadResponse:
        """파일 문서 업로드"""
        try:
            # 파일 크기 검증
            max_file_size = getattr(self.settings, 'max_file_size', 10 * 1024 * 1024)  # 10MB
            if len(request.file_content) > max_file_size:
                return DocumentUploadResponse(
                    success=False,
                    message=f"파일 크기가 최대 허용 크기({max_file_size // (1024*1024)}MB)를 초과합니다",
                    document_ids=[],
                    chunk_count=0
                )

            # 파일 확장자 검증
            allowed_extensions = {'.pdf', '.txt', '.md', '.html', '.htm'}
            file_ext = '.' + request.filename.lower().split('.')[-1] if '.' in request.filename else ''

            if file_ext not in allowed_extensions:
                return DocumentUploadResponse(
                    success=False,
                    message=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}",
                    document_ids=[],
                    chunk_count=0
                )

            # 파일 처리 및 청킹
            documents = self.repository.process_file_content(
                file_content=request.file_content,
                filename=request.filename,
                metadata=request.metadata,
                chunk_size=request.chunk_size,
                chunk_overlap=request.chunk_overlap,
                chunking_strategy=request.chunking_strategy
            )

            # 벡터 저장소에 추가
            document_ids = await self.repository.add_documents(documents, collection_name)

            return DocumentUploadResponse(
                success=True,
                message=f"파일이 {len(documents)}개의 청크로 분할되어 업로드되었습니다",
                document_ids=document_ids,
                chunk_count=len(documents)
            )

        except Exception as e:
            logger.error(f"파일 문서 업로드 실패: {e}")
            return DocumentUploadResponse(
                success=False,
                message=f"파일 업로드 중 오류가 발생했습니다: {str(e)}",
                document_ids=[],
                chunk_count=0
            )

    async def get_document_by_id(
        self,
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[DocumentInfo]:
        """ID로 문서 조회"""
        try:
            return await self.repository.get_document_by_id(document_id, collection_name)
        except Exception as e:
            logger.error(f"문서 조회 실패: {e}")
            return None

    async def update_document(
        self,
        document_id: str,
        request: DocumentUpdateRequest,
        collection_name: Optional[str] = None
    ) -> bool:
        """문서 업데이트"""
        try:
            # 입력 검증
            if not request.content and not request.metadata:
                return False

            return await self.repository.update_document(
                document_id=document_id,
                new_content=request.content,
                new_metadata=request.metadata,
                collection_name=collection_name
            )
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            return False

    async def delete_documents(
        self,
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> DocumentDeleteResponse:
        """문서들 삭제"""
        try:
            if not document_ids:
                return DocumentDeleteResponse(
                    success=False,
                    message="삭제할 문서 ID가 없습니다",
                    deleted_count=0
                )

            success = await self.repository.delete_documents(document_ids, collection_name)

            return DocumentDeleteResponse(
                success=success,
                message=f"{len(document_ids)}개 문서 삭제 {'성공' if success else '실패'}",
                deleted_count=len(document_ids) if success else 0,
                deleted_ids=document_ids if success else []
            )

        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            return DocumentDeleteResponse(
                success=False,
                message=f"문서 삭제 중 오류가 발생했습니다: {str(e)}",
                deleted_count=0
            )

    async def get_documents_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        collection_name: Optional[str] = None,
        limit: int = 100
    ) -> List[DocumentInfo]:
        """메타데이터로 문서들 조회"""
        try:
            return await self.repository.get_documents_by_metadata(
                metadata_filter, collection_name, limit
            )
        except Exception as e:
            logger.error(f"메타데이터 문서 조회 실패: {e}")
            return []

    async def bulk_delete_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        collection_name: Optional[str] = None
    ) -> int:
        """메타데이터 조건으로 대량 삭제"""
        try:
            # 먼저 삭제할 문서들을 조회
            documents = await self.get_documents_by_metadata(
                metadata_filter, collection_name, limit=1000
            )

            if not documents:
                return 0

            # 문서 ID들 추출
            document_ids = [doc.document_id for doc in documents]

            # 문서들 삭제
            result = await self.delete_documents(document_ids, collection_name)

            return result.deleted_count if result.success else 0

        except Exception as e:
            logger.error(f"대량 삭제 실패: {e}")
            return 0