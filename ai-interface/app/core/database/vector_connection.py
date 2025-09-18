# app/core/database/vector_connection.py (최신 langchain-postgres 기반)
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any

from langchain_community.embeddings import OllamaEmbeddings
from langchain_postgres import PGVector
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from app.core.config.settings import Settings

logger = logging.getLogger(__name__)


class VectorConnectionManager:
    """벡터 DB 연결 관리자"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._embeddings: Optional[OllamaEmbeddings] = None
        self._connection_string: Optional[str] = None
        self._async_engine = None
        self._async_session_factory = None
        self._is_initialized = False
        self._lock = asyncio.Lock()
        self._vectorstore_cache: Dict[str, PGVector] = {}

    async def initialize(self) -> None:
        """연결 초기화 (지연 초기화)"""
        if self._is_initialized:
            return

        async with self._lock:
            if self._is_initialized:
                return

            try:
                await self._setup_embeddings()
                await self._setup_database_connection()
                await self._verify_connection()
                await self._ensure_pgvector_extension()
                self._is_initialized = True
                logger.info("벡터 DB 연결 초기화 완료")

            except Exception as e:
                logger.error(f"벡터 DB 연결 초기화 실패: {e}")
                raise

    async def _setup_embeddings(self):
        """임베딩 모델 초기화"""
        self._embeddings = OllamaEmbeddings(
            base_url=self.settings.ollama_base_url,
            model=self.settings.ollama_embedding_model
        )

        # 임베딩 모델 연결 테스트
        try:
            test_embedding = await asyncio.get_event_loop().run_in_executor(
                None, self._embeddings.embed_query, "test"
            )
            logger.info(f"임베딩 모델 '{self.settings.ollama_embedding_model}' 연결 성공")
            logger.info(f"임베딩 차원: {len(test_embedding)}")
        except Exception as e:
            raise ConnectionError(f"Ollama 임베딩 모델 연결 실패: {e}")

    async def _setup_database_connection(self):
        """데이터베이스 연결 설정"""
        # 최신 langchain-postgres는 psycopg3 사용
        self._connection_string = (
            f"postgresql+psycopg://{self.settings.vector_postgres_user}:"
            f"{self.settings.vector_postgres_password}@{self.settings.vector_postgres_host}:"
            f"{self.settings.vector_postgres_port}/{self.settings.vector_postgres_db}"
        )

        # 비동기 연결 엔진 (asyncpg 사용 - 별도 관리 작업용)
        async_connection_string = (
            f"postgresql+asyncpg://{self.settings.vector_postgres_user}:"
            f"{self.settings.vector_postgres_password}@{self.settings.vector_postgres_host}:"
            f"{self.settings.vector_postgres_port}/{self.settings.vector_postgres_db}"
        )

        self._async_engine = create_async_engine(
            async_connection_string,
            poolclass=NullPool,  # 벡터 작업은 장시간 실행될 수 있음
            echo=self.settings.vector_db_echo,
            future=True,
            pool_pre_ping=True,  # 연결 상태 확인
        )

        self._async_session_factory = async_sessionmaker(
            self._async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def _verify_connection(self):
        """연결 검증"""
        try:
            # 비동기 DB 연결 테스트
            async with self._async_engine.begin() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.fetchone()
                logger.info(f"PostgreSQL 연결 성공: {version[0]}")

        except Exception as e:
            raise ConnectionError(f"PostgreSQL 연결 실패: {e}")

    async def _ensure_pgvector_extension(self):
        """pgvector 확장 확인 및 생성"""
        try:
            async with self._async_engine.begin() as conn:
                # pgvector 확장 확인
                result = await conn.execute(
                    text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                )
                exists = result.fetchone()

                if not exists[0]:
                    # pgvector 확장 생성 시도
                    try:
                        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                        logger.info("pgvector 확장 생성 완료")
                    except Exception as e:
                        logger.warning(f"pgvector 확장 생성 실패: {e}")
                        raise ConnectionError(
                            "pgvector 확장이 설치되지 않았습니다. "
                            "PostgreSQL에 pgvector 확장을 설치하거나 "
                            "pgvector/pgvector 도커 이미지를 사용하세요."
                        )
                else:
                    logger.info("pgvector 확장이 이미 설치되어 있습니다")

        except Exception as e:
            if "pgvector 확장" in str(e):
                raise
            logger.error(f"pgvector 확장 확인 실패: {e}")
            raise

    def get_embeddings(self) -> OllamaEmbeddings:
        """임베딩 인스턴스 반환"""
        if not self._is_initialized:
            raise RuntimeError("연결이 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._embeddings

    def get_connection_string(self) -> str:
        """연결 문자열 반환 (PGVector용)"""
        if not self._is_initialized:
            raise RuntimeError("연결이 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        return self._connection_string

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """비동기 DB 세션 컨텍스트 매니저"""
        if not self._is_initialized:
            raise RuntimeError("연결이 초기화되지 않았습니다.")

        async with self._async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_vectorstore(self, collection_name: Optional[str] = None) -> PGVector:
        """벡터스토어 인스턴스 생성 (최신 langchain-postgres 방식)"""
        if not self._is_initialized:
            await self.initialize()

        collection = collection_name or self.settings.default_collection_name

        # 캐시에서 확인
        if collection in self._vectorstore_cache:
            return self._vectorstore_cache[collection]

        # 새로운 벡터스토어 생성
        vectorstore = PGVector(
            embeddings=self._embeddings,
            collection_name=collection,
            connection=self._connection_string,
            use_jsonb=True,  # JSONB 사용으로 메타데이터 검색 성능 향상
        )

        # 캐시에 저장
        self._vectorstore_cache[collection] = vectorstore

        logger.info(f"벡터스토어 생성: collection='{collection}'")
        return vectorstore

    async def get_vectorstore_info(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """벡터스토어 정보 조회"""
        try:
            vectorstore = await self.create_vectorstore(collection_name)

            async with self.get_async_session() as session:
                # 테이블 정보 조회
                collection = collection_name or self.settings.default_collection_name
                table_name = f"langchain_pg_embedding_{collection}"

                result = await session.execute(text(f"""
                    SELECT
                        COUNT(*) as document_count,
                        pg_size_pretty(pg_total_relation_size('{table_name}')) as table_size
                    FROM {table_name}
                """))

                info = result.fetchone()

                return {
                    "collection_name": collection,
                    "document_count": info.document_count if info else 0,
                    "table_size": info.table_size if info else "0 bytes",
                    "embedding_model": self.settings.ollama_embedding_model,
                    "embedding_dimension": len(await asyncio.get_event_loop().run_in_executor(
                        None, self._embeddings.embed_query, "test"
                    ))
                }

        except Exception as e:
            logger.error(f"벡터스토어 정보 조회 실패: {e}")
            return {
                "collection_name": collection_name or self.settings.default_collection_name,
                "document_count": 0,
                "error": str(e)
            }

    async def test_connection(self) -> Dict[str, Any]:
        """연결 테스트"""
        test_results = {
            "postgresql": False,
            "pgvector": False,
            "ollama": False,
            "embedding": False,
            "overall": False
        }

        try:
            # PostgreSQL 연결 테스트
            async with self._async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                test_results["postgresql"] = True

            # pgvector 확장 테스트
            async with self._async_engine.begin() as conn:
                result = await conn.execute(text("SELECT vector_version()"))
                version = result.fetchone()
                test_results["pgvector"] = True
                test_results["pgvector_version"] = version[0] if version else "unknown"

            # Ollama 연결 테스트
            import requests
            response = requests.get(f"{self.settings.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                test_results["ollama"] = True

            # 임베딩 테스트
            if self._embeddings:
                test_embedding = await asyncio.get_event_loop().run_in_executor(
                    None, self._embeddings.embed_query, "connection test"
                )
                test_results["embedding"] = len(test_embedding) > 0
                test_results["embedding_dimension"] = len(test_embedding)

            test_results["overall"] = all([
                test_results["postgresql"],
                test_results["pgvector"],
                test_results["ollama"],
                test_results["embedding"]
            ])

        except Exception as e:
            test_results["error"] = str(e)

        return test_results

    async def close(self):
        """연결 종료"""
        try:
            # 캐시 정리
            self._vectorstore_cache.clear()

            # 비동기 엔진 종료
            if self._async_engine:
                await self._async_engine.dispose()

            self._is_initialized = False
            logger.info("벡터 DB 연결 종료")

        except Exception as e:
            logger.error(f"벡터 DB 연결 종료 중 오류: {e}")
