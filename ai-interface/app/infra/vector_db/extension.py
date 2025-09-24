from sqlalchemy import text

from app.infra.vector_db.connection import PostgresConnectionManager


class PostgresExtensionManager:
    """PostgreSQL 확장 관리만 담당"""

    def __init__(self, connection_manager: PostgresConnectionManager):
        self.connection_manager = connection_manager

    async def ensure_pgvector_extension(self):
        """pgvector 확장 확인 및 생성"""
        engine = await self.connection_manager.get_engine()
        async with engine.begin() as conn:
            # pgvector 확장이 이미 있는지 확인
            result = await conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )

            if not result.fetchone():
                # pgvector 확장 생성
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
