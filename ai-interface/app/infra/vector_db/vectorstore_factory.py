# infra/vector_db/vectorstore_factory.py
import asyncio
from typing import Dict

from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVectorStore

from app.core.config.settings import Settings
from app.infra.vector_db.connection import PostgresConnectionManager


class VectorStoreFactory:
    """PGVectorStore 팩토리 - 컬렉션별 인스턴스 관리"""

    def __init__(self,
                 connection_manager: PostgresConnectionManager,
                 settings: Settings,
                 embeddings: OllamaEmbeddings):
        self.connection_manager = connection_manager
        self.embeddings = embeddings
        self.settings = settings
        self._cache: Dict[str, PGVectorStore] = {}
        self._lock = asyncio.Lock()

    async def get_vectorstore(self, collection_name: str = "default") -> PGVectorStore:
        """컬렉션별 벡터스토어 반환 (캐싱)"""
        # 캐시 확인 (락 없이)
        if collection_name in self._cache:
            return self._cache[collection_name]

        # 락으로 보호된 생성
        async with self._lock:
            # 더블 체크 패턴
            if collection_name in self._cache:
                return self._cache[collection_name]

            # 새 인스턴스 생성
            engine = await self.connection_manager.get_engine()
            # 테이블 명시적 초기화
            table_name = f"{self.settings.vector_table_prefix}{collection_name}"

            vectorstore = await PGVectorStore.create(
                engine=engine,
                table_name=table_name,
                embedding_service=self.embeddings,
            )

            self._cache[collection_name] = vectorstore
            return vectorstore

    def clear_cache(self):
        """캐시 정리"""
        self._cache.clear()

    def get_cached_collections(self) -> list[str]:
        """캐시된 컬렉션 목록"""
        return list(self._cache.keys())
