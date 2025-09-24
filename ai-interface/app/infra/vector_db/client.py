# infra/vector_db/client.py
import asyncio
from typing import Optional

from langchain_ollama import OllamaEmbeddings
from langchain_postgres import PGVectorStore

from app.core.config.settings import Settings
from app.infra.vector_db.connection import PostgresConnectionManager
from app.infra.vector_db.vectorstore_factory import VectorStoreFactory


class VectorDBClient:
    """벡터DB 클라이언트"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.connection_manager = PostgresConnectionManager(settings)
        # self.extension_manager = PostgresExtensionManager(self.connection_manager)
        self._vectorstore_factory: Optional[VectorStoreFactory] = None
        self._is_initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self):
        """한 번만 초기화"""
        if self._is_initialized:
            return

        async with self._lock:
            if self._is_initialized:
                return

            # 확장 확인
            # await self.extension_manager.ensure_pgvector_extension()

            # 팩토리 생성
            embeddings = self._get_embeddings()
            self._vectorstore_factory = VectorStoreFactory(
                self.connection_manager,
                self.settings,
                embeddings
            )

            self._is_initialized = True

    async def get_vectorstore(self, collection_name: str = None) -> PGVectorStore:
        """벡터스토어 반환 (캐싱됨)"""
        if not self._is_initialized:
            await self.initialize()

        collection = collection_name or self.settings.default_collection_name
        return await self._vectorstore_factory.get_vectorstore(collection)

    def _get_embeddings(self) -> OllamaEmbeddings:
        """Ollama 임베딩 서비스 생성"""
        return OllamaEmbeddings(
            model=self.settings.ollama_embedding_model,
            base_url=self.settings.ollama_base_url
        )

    async def close(self):
        """리소스 정리"""
        if self._vectorstore_factory:
            self._vectorstore_factory.clear_cache()
        await self.connection_manager.close()
