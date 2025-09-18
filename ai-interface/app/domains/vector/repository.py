# app/domains/vector/repository.py (통합된 비동기 리포지토리)
import asyncio
import logging
import time
import uuid
from typing import List, Optional, Dict, Any

from langchain_core.documents import Document

from app.core.database.vector_connection import VectorConnectionManager
from .schemas import SearchResult

logger = logging.getLogger(__name__)


class VectorRepository:
    """통합된 비동기 벡터 리포지토리 (PGVector 기반)"""

    def __init__(self, connection_manager: VectorConnectionManager):
        self.connection_manager = connection_manager

    async def add_documents(
            self,
            documents: List[Document],
            collection_name: Optional[str] = None
    ) -> List[str]:
        """문서 벡터 저장"""
        try:
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)

            # 문서에 고유 ID 추가
            document_ids = []
            for doc in documents:
                if "document_id" not in doc.metadata:
                    doc_id = str(uuid.uuid4())
                    doc.metadata["document_id"] = doc_id
                else:
                    doc_id = doc.metadata["document_id"]

                doc.metadata["created_at"] = time.time()
                document_ids.append(doc_id)

            # 배치 처리로 성능 최적화
            batch_size = self.connection_manager.settings.vector_batch_size
            all_ids = []

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_doc_ids = document_ids[i:i + batch_size]

                # 비동기 실행
                batch_ids = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda b=batch, ids=batch_doc_ids: vectorstore.add_documents(b, ids=ids)
                )
                all_ids.extend(batch_ids)

                logger.debug(f"배치 {i // batch_size + 1} 처리 완료: {len(batch)}개 문서")

            logger.info(f"총 {len(documents)}개 문서를 컬렉션 '{collection_name or 'default'}'에 저장 완료")
            return all_ids

        except Exception as e:
            logger.error(f"문서 저장 실패: {e}")
            raise

    async def search(
            self,
            query: str,
            k: int = 5,
            collection_name: Optional[str] = None,
            metadata_filter: Optional[Dict[str, Any]] = None,
            score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """벡터 유사도 검색"""
        try:
            start_time = time.time()
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)

            # 검색 함수 생성
            search_func = self._create_search_function(
                vectorstore, query, k, metadata_filter
            )

            # 비동기 실행
            results = await asyncio.get_event_loop().run_in_executor(
                None, search_func
            )

            # 결과 변환 및 필터링
            search_results = []
            for doc, score in results:
                # 점수 임계값 필터링 (유사도가 높을수록 점수가 낮음)
                if score_threshold is not None and score > score_threshold:
                    continue

                search_results.append(SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=float(score),
                    document_id=doc.metadata.get("document_id")
                ))

            execution_time = (time.time() - start_time) * 1000
            logger.info(f"검색 완료: {len(search_results)}개 결과, {execution_time:.2f}ms")

            return search_results

        except Exception as e:
            logger.error(f"검색 실패: {e}")
            raise

    def _create_search_function(self, vectorstore, query, k, metadata_filter):
        """검색 함수 생성"""

        def search_func():
            if metadata_filter:
                return vectorstore.similarity_search_with_score(
                    query, k=k, filter=metadata_filter
                )
            else:
                return vectorstore.similarity_search_with_score(query, k=k)

        return search_func

    async def delete_documents(
            self,
            document_ids: List[str],
            collection_name: Optional[str] = None
    ) -> bool:
        """문서 삭제"""
        try:
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)

            # 비동기 실행
            delete_func = lambda: vectorstore.delete(ids=document_ids)
            await asyncio.get_event_loop().run_in_executor(None, delete_func)

            logger.info(f"문서 삭제 완료: {len(document_ids)}개")
            return True

        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            return False

    async def search_by_vector(
            self,
            embedding: List[float],
            k: int = 5,
            collection_name: Optional[str] = None,
            metadata_filter: Optional[Dict[str, Any]] = None,
            score_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """벡터로 직접 검색"""
        try:
            start_time = time.time()
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)

            # 벡터 검색 함수 생성
            search_func = self._create_vector_search_function(
                vectorstore, embedding, k, metadata_filter
            )

            # 비동기 실행
            results = await asyncio.get_event_loop().run_in_executor(
                None, search_func
            )

            # 결과 변환 및 필터링
            search_results = []
            for doc, score in results:
                if score_threshold is not None and score > score_threshold:
                    continue

                search_results.append(SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=float(score),
                    document_id=doc.metadata.get("document_id")
                ))

            execution_time = (time.time() - start_time) * 1000
            logger.info(f"벡터 검색 완료: {len(search_results)}개 결과, {execution_time:.2f}ms")

            return search_results

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            raise

    def _create_vector_search_function(self, vectorstore, embedding, k, metadata_filter):
        """벡터 검색 함수 생성"""

        def search_func():
            if metadata_filter:
                return vectorstore.similarity_search_by_vector_with_score(
                    embedding, k=k, filter=metadata_filter
                )
            else:
                return vectorstore.similarity_search_by_vector_with_score(embedding, k=k)

        return search_func

    async def get_document_by_id(
            self,
            document_id: str,
            collection_name: Optional[str] = None
    ) -> Optional[Document]:
        """ID로 문서 조회"""
        try:
            results = await self.search(
                query="",  # 빈 쿼리
                k=1,
                collection_name=collection_name,
                metadata_filter={"document_id": {"$eq": document_id}}
            )

            if results:
                result = results[0]
                return Document(
                    page_content=result.content,
                    metadata=result.metadata
                )
            return None

        except Exception as e:
            logger.error(f"문서 조회 실패: {e}")
            return None

    async def get_documents_by_metadata(
            self,
            metadata_filter: Dict[str, Any],
            collection_name: Optional[str] = None,
            limit: int = 100
    ) -> List[Document]:
        """메타데이터 조건으로 문서 조회"""
        try:
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)

            # 메타데이터 검색 함수
            search_func = lambda: vectorstore.get_by_ids(
                ids=[],  # 빈 IDs로 메타데이터 필터만 사용
                filter=metadata_filter
            )

            # 비동기 실행
            documents = await asyncio.get_event_loop().run_in_executor(
                None, search_func
            )

            logger.info(f"메타데이터 검색 완료: {len(documents)}개 문서")
            return documents[:limit]

        except Exception as e:
            logger.error(f"메타데이터 검색 실패: {e}")
            return []

    async def update_document(
            self,
            document_id: str,
            new_content: Optional[str] = None,
            new_metadata: Optional[Dict[str, Any]] = None,
            collection_name: Optional[str] = None
    ) -> bool:
        """문서 업데이트"""
        try:
            # 기존 문서 조회
            existing_doc = await self.get_document_by_id(document_id, collection_name)
            if not existing_doc:
                logger.warning(f"업데이트할 문서를 찾을 수 없음: {document_id}")
                return False

            # 새로운 문서 생성
            updated_content = new_content or existing_doc.page_content
            updated_metadata = existing_doc.metadata.copy()

            if new_metadata:
                updated_metadata.update(new_metadata)

            updated_metadata["updated_at"] = time.time()

            updated_doc = Document(
                page_content=updated_content,
                metadata=updated_metadata
            )

            # 기존 문서 삭제 후 새 문서 추가
            await self.delete_documents([document_id], collection_name)
            await self.add_documents([updated_doc], collection_name)

            logger.info(f"문서 업데이트 완료: {document_id}")
            return True

        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            return False

    async def get_status(self) -> Dict[str, Any]:
        """저장소 상태 조회"""
        try:
            # 연결 테스트
            test_results = await self.connection_manager.test_connection()

            # 벡터스토어 정보
            vectorstore_info = await self.connection_manager.get_vectorstore_info()

            return {
                "is_connected": test_results.get("overall", False),
                "embedding_model": self.connection_manager.settings.ollama_embedding_model,
                "embedding_dimension": test_results.get("embedding_dimension", 0),
                "pgvector_version": test_results.get("pgvector_version", "unknown"),
                "total_documents": vectorstore_info.get("document_count", 0),
                "collection_count": len(self.connection_manager._vectorstore_cache),
                "connection_tests": test_results,
                "vectorstore_info": vectorstore_info
            }

        except Exception as e:
            logger.error(f"상태 조회 실패: {e}")
            return {
                "is_connected": False,
                "error": str(e)
            }

    async def get_collection_stats(
            self,
            collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """컬렉션 통계 조회"""
        try:
            vectorstore_info = await self.connection_manager.get_vectorstore_info(collection_name)

            # 추가 통계 정보
            async with self.connection_manager.get_async_session() as session:
                collection = collection_name or self.connection_manager.settings.default_collection_name
                table_name = f"langchain_pg_embedding_{collection}"

                # 메타데이터 분포 조회
                result = await session.execute(f"""
                    SELECT 
                        COUNT(*) as total_count,
                        COUNT(DISTINCT cmetadata) as unique_metadata_count,
                        MIN(created_at) as oldest_document,
                        MAX(created_at) as newest_document
                    FROM {table_name}
                    WHERE cmetadata ? 'created_at'
                """)

                stats = await result.fetchone()

                return {
                    "collection_name": collection,
                    "total_documents": stats.total_count if stats else 0,
                    "unique_metadata_variants": stats.unique_metadata_count if stats else 0,
                    "oldest_document": stats.oldest_document if stats else None,
                    "newest_document": stats.newest_document if stats else None,
                    **vectorstore_info
                }

        except Exception as e:
            logger.error(f"컬렉션 통계 조회 실패: {e}")
            return {
                "collection_name": collection_name or "default",
                "error": str(e)
            }

    async def create_collection(self, collection_name: str) -> bool:
        """컬렉션 생성"""
        try:
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)
            logger.info(f"컬렉션 생성: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"컬렉션 생성 실패: {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """컬렉션 삭제"""
        try:
            vectorstore = await self.connection_manager.create_vectorstore(collection_name)

            # 컬렉션 삭제 (테이블 삭제)
            delete_func = lambda: vectorstore.delete_collection()
            await asyncio.get_event_loop().run_in_executor(None, delete_func)

            # 캐시에서 제거
            self.connection_manager._vectorstore_cache.pop(collection_name, None)

            logger.info(f"컬렉션 삭제: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {e}")
            return False

    async def list_collections(self) -> List[str]:
        """모든 컬렉션 목록 조회"""
        try:
            async with self.connection_manager.get_async_session() as session:
                # langchain_pg_embedding으로 시작하는 테이블 조회
                result = await session.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name LIKE 'langchain_pg_embedding_%'
                    AND table_schema = 'public'
                """)

                tables = await result.fetchall()

                # 테이블명에서 컬렉션명 추출
                collections = []
                for table in tables:
                    table_name = table.table_name
                    if table_name.startswith('langchain_pg_embedding_'):
                        collection_name = table_name.replace('langchain_pg_embedding_', '')
                        collections.append(collection_name)

                logger.info(f"컬렉션 목록 조회 완료: {len(collections)}개")
                return collections

        except Exception as e:
            logger.error(f"컬렉션 목록 조회 실패: {e}")
            return []

    async def bulk_delete_by_metadata(
            self,
            metadata_filter: Dict[str, Any],
            collection_name: Optional[str] = None
    ) -> int:
        """메타데이터 조건으로 대량 삭제"""
        try:
            # 조건에 맞는 문서들 조회
            documents = await self.get_documents_by_metadata(
                metadata_filter, collection_name, limit=10000
            )

            if not documents:
                logger.info("삭제할 문서가 없습니다")
                return 0

            # 문서 ID 추출
            document_ids = [doc.metadata.get("document_id") for doc in documents if doc.metadata.get("document_id")]

            if document_ids:
                await self.delete_documents(document_ids, collection_name)
                logger.info(f"메타데이터 조건으로 {len(document_ids)}개 문서 삭제 완료")
                return len(document_ids)

            return 0

        except Exception as e:
            logger.error(f"대량 삭제 실패: {e}")
            return 0

    async def close(self):
        """리소스 정리"""
        try:
            await self.connection_manager.close()
            logger.info("벡터 리포지토리 정리 완료")
        except Exception as e:
            logger.error(f"벡터 리포지토리 정리 실패: {e}")
