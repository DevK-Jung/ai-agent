import logging
from typing import List

from sqlalchemy import text

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

    async def list_collections(self) -> List[str]:
        """컬렉션 목록 조회"""
        try:
            engine = await self.connection_manager.get_engine()

            # PGEngine의 내부 연결 풀 사용 todo 내부 메서드라 버전 업할경우 에러날 수있음
            async with engine._pool.connect() as conn:
                # 테이블명 패턴으로 조회
                result = await conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE :prefix
                    ORDER BY table_name
                """), {"prefix": f"{self.settings.vector_table_prefix}%"})

                tables = result.fetchall()

                # 프리픽스 제거해서 컬렉션명만 반환
                collections = []
                prefix_len = len(self.settings.vector_table_prefix)
                for row in tables:
                    table_name = row[0]
                    collection_name = table_name[prefix_len:]
                    collections.append(collection_name)

                await conn.commit()  # 트랜잭션 커밋

                logger.info(f"발견된 컬렉션: {len(collections)}개")
                return collections

        except Exception as e:
            logger.error(f"컬렉션 목록 조회 에러: {e}")
            return []

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
