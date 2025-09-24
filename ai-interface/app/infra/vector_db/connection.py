# infra/vector_db/connection.py
import asyncio
from typing import Optional

from langchain_postgres import PGEngine
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config.settings import Settings


class PostgresConnectionManager:
    """PostgreSQL 연결 관리 (싱글톤)"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pg_engine: Optional[PGEngine] = None
        self._lock = asyncio.Lock()

    async def get_engine(self) -> PGEngine:
        """PGEngine 반환 (캐싱됨)"""
        if self._pg_engine is None:
            await self._create_engine()
        return self._pg_engine

    async def _create_engine(self):
        """PGEngine 생성 (한 번만)"""
        async with self._lock:
            if self._pg_engine is not None:
                return

            async_engine = create_async_engine(
                self.settings.vector_async_connection_string,
                pool_size=self.settings.vector_connection_pool_size,
                max_overflow=self.settings.vector_max_overflow,
                pool_pre_ping=True,
                echo=self.settings.vector_db_echo,
            )

            self._pg_engine = PGEngine.from_engine(engine=async_engine)

    async def close(self):
        """리소스 정리"""
        if self._pg_engine:
            await self._pg_engine.close()
            self._pg_engine = None
