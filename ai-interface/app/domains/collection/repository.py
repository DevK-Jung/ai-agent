import logging

from ...core.config.settings import Settings
from ...infra.vector_db.connection import PostgresConnectionManager

logger = logging.getLogger(__name__)


class CollectionRepository:

    def __init__(self,
                 settings: Settings,
                 connection_manager: PostgresConnectionManager):
        self.settings = settings
        self.connection_manager = connection_manager

    def _get_collection_name(self, collection_name: str):
        return f"{self.settings.vector_table_prefix}{collection_name}"

    async def create_collection(
            self,
            collection_name: str,
            vector_size: int = 768,
    ) -> bool:
        """컬렉션 테이블 생성 및 초기화"""
        try:
            engine = await self.connection_manager.get_engine()
            table_name = self._get_collection_name(collection_name)

            await engine.ainit_vectorstore_table(
                table_name=table_name,
                vector_size=vector_size,
            )

            logger.info(f"테이블 초기화 완료: {table_name}")
            return True

        except Exception as e:
            logger.error(f"테이블 초기화 에러: {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """컬렉션 테이블 삭제"""
        try:
            engine = await self.connection_manager.get_engine()
            table_name = self._get_collection_name(collection_name)

            await engine.adrop_table(table_name)

            logger.info(f"테이블 삭제 완료: {table_name}")
            return True

        except Exception as e:
            logger.error(f"테이블 삭제 에러: {e}")
            return False
