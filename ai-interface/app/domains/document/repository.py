import logging
import tempfile
import uuid
from typing import List, Optional, Dict, Any

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader

from app.infra.vector_db.client import VectorDBClient
from app.domains.document.constants import ChunkingStrategy
from .schemas import DocumentInfo

logger = logging.getLogger(__name__)


class DocumentRepository:
    """문서 리포지토리 - 저수준 데이터 액세스"""

    def __init__(self, vector_db_client: VectorDBClient):
        self.vector_db_client = vector_db_client

    async def add_documents(
        self,
        documents: List[Document],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """문서들을 벡터 저장소에 추가"""
        try:
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            # 각 문서에 고유 ID 할당
            document_ids = []
            for doc in documents:
                doc_id = str(uuid.uuid4())
                doc.metadata["document_id"] = doc_id
                document_ids.append(doc_id)

            # 벡터 저장소에 추가
            await vectorstore.aadd_documents(documents)

            return document_ids

        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise

    async def get_document_by_id(
        self,
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[DocumentInfo]:
        """ID로 문서 조회"""
        try:
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            # 메타데이터 필터로 문서 검색
            docs = await vectorstore.asimilarity_search(
                query="",
                k=1,
                filter={"document_id": document_id}
            )

            if docs:
                doc = docs[0]
                return DocumentInfo(
                    document_id=document_id,
                    content=doc.page_content,
                    metadata=doc.metadata,
                    collection_name=collection_name
                )

            return None

        except Exception as e:
            logger.error(f"문서 조회 실패: {e}")
            return None

    async def update_document(
        self,
        document_id: str,
        new_content: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
        collection_name: Optional[str] = None
    ) -> bool:
        """문서 업데이트"""
        try:
            # TODO: 실제 문서 업데이트 로직 구현
            # 현재는 삭제 후 재추가 방식으로 구현 가능
            return True
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            return False

    async def delete_documents(
        self,
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> bool:
        """문서들 삭제"""
        try:
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            # 각 문서 ID로 삭제
            for doc_id in document_ids:
                # TODO: 실제 삭제 로직 구현 (PGVector delete 메서드)
                pass

            return True

        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            return False

    async def get_documents_by_metadata(
        self,
        metadata_filter: Dict[str, Any],
        collection_name: Optional[str] = None,
        limit: int = 100
    ) -> List[DocumentInfo]:
        """메타데이터로 문서들 조회"""
        try:
            vectorstore = await self.vector_db_client.get_vectorstore(collection_name)

            docs = await vectorstore.asimilarity_search(
                query="",
                k=limit,
                filter=metadata_filter
            )

            return [
                DocumentInfo(
                    document_id=doc.metadata.get("document_id", ""),
                    content=doc.page_content,
                    metadata=doc.metadata,
                    collection_name=collection_name
                )
                for doc in docs
            ]

        except Exception as e:
            logger.error(f"메타데이터 문서 조회 실패: {e}")
            return []

    def process_text_content(
        self,
        content: str,
        filename: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER
    ) -> List[Document]:
        """텍스트 내용을 문서로 처리"""
        try:
            # 기본 메타데이터 설정
            doc_metadata = metadata or {}
            if filename:
                doc_metadata["filename"] = filename
            doc_metadata["type"] = "text"

            # 청킹 전략에 따라 텍스트 분할
            documents = self._split_text(
                content, chunking_strategy, chunk_size, chunk_overlap
            )

            # 각 청크에 메타데이터 추가
            for i, doc in enumerate(documents):
                doc.metadata.update(doc_metadata)
                doc.metadata["chunk_index"] = i

            return documents

        except Exception as e:
            logger.error(f"텍스트 처리 실패: {e}")
            raise

    def process_file_content(
        self,
        file_content: bytes,
        filename: str,
        metadata: Dict[str, Any] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        chunking_strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE_CHARACTER
    ) -> List[Document]:
        """파일 내용을 문서로 처리"""
        try:
            # 기본 메타데이터 설정
            doc_metadata = metadata or {}
            doc_metadata["filename"] = filename
            doc_metadata["file_size"] = len(file_content)

            # 파일 확장자에 따른 처리
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''

            if file_ext == 'pdf':
                documents = self._process_pdf_content(file_content, doc_metadata)
            else:
                # 텍스트 파일로 처리
                text_content = file_content.decode('utf-8')
                doc_metadata["type"] = "text"
                documents = self._split_text(
                    text_content, chunking_strategy, chunk_size, chunk_overlap
                )

            # 각 청크에 메타데이터 추가
            for i, doc in enumerate(documents):
                doc.metadata.update(doc_metadata)
                doc.metadata["chunk_index"] = i

            return documents

        except Exception as e:
            logger.error(f"파일 처리 실패: {e}")
            raise

    def _process_pdf_content(
        self,
        file_content: bytes,
        metadata: Dict[str, Any]
    ) -> List[Document]:
        """PDF 파일 처리"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()

            loader = PyPDFLoader(temp_file.name)
            documents = loader.load()

            # 메타데이터에 PDF 타입 추가
            for doc in documents:
                doc.metadata.update(metadata)
                doc.metadata["type"] = "pdf"

            return documents

    def _split_text(
        self,
        text: str,
        chunking_strategy: ChunkingStrategy,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List[Document]:
        """텍스트 분할"""
        # 기본값 설정
        default_chunk_size = 1000 if chunking_strategy == ChunkingStrategy.RECURSIVE_CHARACTER else 200
        default_overlap = 100 if chunking_strategy == ChunkingStrategy.RECURSIVE_CHARACTER else 50

        chunk_size = chunk_size or default_chunk_size
        chunk_overlap = chunk_overlap or default_overlap

        # 분할 전략에 따른 처리
        if chunking_strategy == ChunkingStrategy.RECURSIVE_CHARACTER:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )
        elif chunking_strategy == ChunkingStrategy.TOKEN:
            text_splitter = TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
        else:
            # 기본값: RECURSIVE_CHARACTER
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
            )

        return text_splitter.create_documents([text])