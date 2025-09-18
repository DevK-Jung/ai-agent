# app/domains/vector/service.py (재구성된 벡터 서비스)
import logging
import os
import tempfile
import time
import uuid
from typing import List, Optional, Dict, Any

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader

from app.core.config.settings import Settings
from app.domains.vector.repository import VectorRepository
from .constants import ChunkingStrategy, DocumentType
from .schemas import (
    DocumentRequest, DocumentResponse, SearchRequest, SearchResponse,
    VectorStoreStatus
)

logger = logging.getLogger(__name__)


class VectorService:
    """벡터 서비스 레이어 (비즈니스 로직)"""

    def __init__(self, repository: VectorRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    def _create_text_splitter(
            self,
            strategy: ChunkingStrategy,
            chunk_size: int,
            chunk_overlap: int
    ):
        """텍스트 분할기 생성"""
        if strategy == ChunkingStrategy.RECURSIVE_CHARACTER:
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
        elif strategy == ChunkingStrategy.TOKEN_BASED:
            return TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            raise ValueError(f"지원하지 않는 분할 전략: {strategy}")

    def _prepare_documents(
            self,
            content: str,
            metadata: Optional[Dict[str, Any]],
            document_type: DocumentType,
            chunk_size: int,
            chunk_overlap: int,
            chunking_strategy: ChunkingStrategy
    ) -> List[Document]:
        """문서 준비 및 분할"""

        # 기본 메타데이터 설정
        doc_metadata = metadata or {}
        document_id = str(uuid.uuid4())
        doc_metadata.update({
            "document_id": document_id,
            "document_type": document_type.value,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "created_at": time.time(),
            "chunking_strategy": chunking_strategy.value
        })

        # Document 객체 생성
        document = Document(
            page_content=content,
            metadata=doc_metadata
        )

        # 텍스트 분할
        text_splitter = self._create_text_splitter(
            strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        chunks = text_splitter.split_documents([document])

        # 각 청크에 추가 메타데이터 설정
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{i}"
            chunk.metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_id": chunk_id,
                "original_document_id": document_id,  # 원본 문서 ID 보존
                "document_id": chunk_id  # 각 청크마다 고유한 ID 사용
            })

        logger.info(f"문서를 {len(chunks)}개 청크로 분할 완료")
        return chunks

    async def add_text_document(
            self,
            request: DocumentRequest,
            collection_name: Optional[str] = None
    ) -> DocumentResponse:
        """텍스트 문서 추가"""

        # 설정값 결정
        chunk_size = request.chunk_size or self.settings.default_chunk_size
        chunk_overlap = request.chunk_overlap or self.settings.default_chunk_overlap

        # 검증
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap은 chunk_size보다 작아야 합니다")

        try:
            # 문서 준비
            documents = self._prepare_documents(
                content=request.content,
                metadata=request.metadata,
                document_type=request.document_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunking_strategy=request.chunking_strategy
            )

            # 벡터 저장
            document_ids = await self.repository.add_documents(
                documents=documents,
                collection_name=collection_name
            )

            return DocumentResponse(
                document_id=documents[0].metadata["document_id"],
                chunks_count=len(documents),
                message=f"문서가 성공적으로 {len(documents)}개 청크로 저장되었습니다",
                metadata={
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "chunking_strategy": request.chunking_strategy.value,
                    "vector_ids": document_ids,
                    "collection_name": collection_name or self.settings.default_collection_name
                }
            )

        except Exception as e:
            logger.error(f"텍스트 문서 추가 실패: {e}")
            raise

    async def add_file_document(
            self,
            file_content: bytes,
            filename: str,
            metadata: Optional[Dict[str, Any]] = None,
            chunk_size: Optional[int] = None,
            chunk_overlap: Optional[int] = None,
            chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER,
            collection_name: Optional[str] = None
    ) -> DocumentResponse:
        """파일 문서 추가"""

        # 설정값 결정
        chunk_size = chunk_size or self.settings.default_chunk_size
        chunk_overlap = chunk_overlap or self.settings.default_chunk_overlap

        # 파일 확장자에 따른 문서 타입 결정
        file_ext = filename.lower().split('.')[-1]
        if file_ext == 'pdf':
            document_type = DocumentType.PDF
        elif file_ext in ['txt', 'md']:
            document_type = DocumentType.TEXT
        elif file_ext in ['html', 'htm']:
            document_type = DocumentType.HTML
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")

        # 임시 파일 생성 및 처리
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        try:
            # 파일 로더 생성
            if document_type == DocumentType.PDF:
                loader = PyPDFLoader(tmp_file_path)
            else:
                loader = TextLoader(tmp_file_path, encoding='utf-8')

            # 문서 로드
            documents = loader.load()

            # 모든 문서 내용 결합
            combined_content = "\n\n".join([doc.page_content for doc in documents])

            # 메타데이터 준비
            file_metadata = metadata or {}
            file_metadata.update({
                "filename": filename,
                "file_type": file_ext,
                "file_size": len(file_content),
                "source": "file_upload"
            })

            # 문서 요청 객체 생성
            request = DocumentRequest(
                content=combined_content,
                metadata=file_metadata,
                document_type=document_type,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                chunking_strategy=chunking_strategy
            )

            # 텍스트 문서로 처리
            return await self.add_text_document(request, collection_name)

        finally:
            # 임시 파일 삭제
            os.unlink(tmp_file_path)

    async def search_documents(
            self,
            request: SearchRequest
    ) -> SearchResponse:
        """문서 검색"""

        start_time = time.time()

        try:
            # 검색 실행
            results = await self.repository.search(
                query=request.query,
                k=min(request.k, self.settings.max_search_k),
                collection_name=request.collection_name,
                metadata_filter=request.metadata_filter,
                score_threshold=request.score_threshold
            )

            execution_time = (time.time() - start_time) * 1000

            return SearchResponse(
                query=request.query,
                results=results,
                total_results=len(results),
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            raise

    async def search_by_vector(
            self,
            embedding: List[float],
            k: int = 5,
            collection_name: Optional[str] = None,
            metadata_filter: Optional[Dict[str, Any]] = None,
            score_threshold: Optional[float] = None
    ) -> SearchResponse:
        """벡터로 직접 검색"""

        start_time = time.time()

        try:
            results = await self.repository.search_by_vector(
                embedding=embedding,
                k=min(k, self.settings.max_search_k),
                collection_name=collection_name,
                metadata_filter=metadata_filter,
                score_threshold=score_threshold
            )

            execution_time = (time.time() - start_time) * 1000

            return SearchResponse(
                query="[벡터 검색]",
                results=results,
                total_results=len(results),
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            raise

    async def get_document_by_id(
            self,
            document_id: str,
            collection_name: Optional[str] = None
    ) -> Optional[Document]:
        """ID로 문서 조회"""
        try:
            return await self.repository.get_document_by_id(document_id, collection_name)
        except Exception as e:
            logger.error(f"문서 조회 실패: {e}")
            raise

    async def update_document(
            self,
            document_id: str,
            new_content: Optional[str] = None,
            new_metadata: Optional[Dict[str, Any]] = None,
            collection_name: Optional[str] = None
    ) -> bool:
        """문서 업데이트"""
        try:
            return await self.repository.update_document(
                document_id=document_id,
                new_content=new_content,
                new_metadata=new_metadata,
                collection_name=collection_name
            )
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            raise

    async def delete_documents(
            self,
            document_ids: List[str],
            collection_name: Optional[str] = None
    ) -> bool:
        """문서 삭제"""
        try:
            return await self.repository.delete_documents(
                document_ids=document_ids,
                collection_name=collection_name
            )
        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            raise

    async def bulk_delete_by_metadata(
            self,
            metadata_filter: Dict[str, Any],
            collection_name: Optional[str] = None
    ) -> int:
        """메타데이터 조건으로 대량 삭제"""
        try:
            return await self.repository.bulk_delete_by_metadata(
                metadata_filter=metadata_filter,
                collection_name=collection_name
            )
        except Exception as e:
            logger.error(f"대량 삭제 실패: {e}")
            raise

    async def get_status(self) -> VectorStoreStatus:
        """벡터 저장소 상태 조회"""
        try:
            status_data = await self.repository.get_status()

            return VectorStoreStatus(
                is_connected=status_data.get("is_connected", False),
                collection_count=status_data.get("collection_count", 0),
                total_documents=status_data.get("total_documents", 0),
                embedding_model=status_data.get("embedding_model", "unknown"),
                status_message=status_data.get("status_message",
                                               "OK" if status_data.get("is_connected") else "Disconnected")
            )

        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return VectorStoreStatus(
                is_connected=False,
                collection_count=0,
                total_documents=0,
                embedding_model="unknown",
                status_message=f"Error: {str(e)}"
            )

    async def get_collection_stats(
            self,
            collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """컬렉션 통계 조회"""
        try:
            return await self.repository.get_collection_stats(collection_name)
        except Exception as e:
            logger.error(f"컬렉션 통계 조회 실패: {e}")
            raise

    async def list_collections(self) -> List[str]:
        """컬렉션 목록 조회"""
        try:
            return await self.repository.list_collections()
        except Exception as e:
            logger.error(f"컬렉션 목록 조회 실패: {e}")
            raise

    async def create_collection(self, collection_name: str) -> bool:
        """컬렉션 생성"""
        try:
            return await self.repository.create_collection(collection_name)
        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {e}")
            raise

    async def delete_collection(self, collection_name: str) -> bool:
        """컬렉션 삭제"""
        try:
            return await self.repository.delete_collection(collection_name)
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {e}")
            raise

    async def get_documents_by_metadata(
            self,
            metadata_filter: Dict[str, Any],
            collection_name: Optional[str] = None,
            limit: int = 100
    ) -> List[Document]:
        """메타데이터 조건으로 문서 조회"""
        try:
            return await self.repository.get_documents_by_metadata(
                metadata_filter=metadata_filter,
                collection_name=collection_name,
                limit=limit
            )
        except Exception as e:
            logger.error(f"메타데이터 검색 실패: {e}")
            raise
