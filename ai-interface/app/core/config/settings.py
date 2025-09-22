# app/core/config/settings.py (통합된 설정)
import os
from functools import lru_cache
from typing import List, Set

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings

from app.core.config.environment import Environment


def get_environment() -> Environment:
    """현재 환경 반환"""
    env_str = os.getenv("ENVIRONMENT", "development").lower()

    # 별칭 처리
    env_aliases = {
        "dev": Environment.DEVELOPMENT,
        "prod": Environment.PRODUCTION,
        "test": Environment.TESTING
    }

    if env_str in env_aliases:
        return env_aliases[env_str]

    try:
        return Environment(env_str)
    except ValueError:
        return Environment.DEVELOPMENT


def get_env_file() -> str:
    """환경에 따라 적절한 .env 파일 경로 반환"""
    environment = get_environment()
    env_file = environment.env_file

    # 파일이 존재하지 않으면 기본 .env 사용
    if not os.path.exists(env_file):
        return ".env"

    return env_file


def parse_comma_list(value):
    """쉼표로 구분된 문자열을 리스트로 변환하는 헬퍼 함수"""
    return [x.strip() for x in value.split(',')] if isinstance(value, str) else value


class Settings(BaseSettings):
    # 기본 애플리케이션 설정
    app_name: str = "FastAPI Application"
    version: str = "1.0.0"
    reload: bool = True

    # 환경 설정
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # 서버 설정
    host: str = "127.0.0.1"
    port: int = 8000

    # 데이터베이스 설정
    database_url: str = "sqlite:///./app.db"
    database_echo: bool = False

    # JWT 설정
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS 설정 (콤마로 구분된 문자열을 리스트로 변환)
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"

    @property
    def cors_origins(self) -> List[str]:
        """CORS 허용 오리진 리스트"""
        origins_str = os.getenv("ALLOWED_ORIGINS", self.allowed_origins)
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "app.log"

    # ========================================
    # 파일 관련 설정
    # ========================================

    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024
    max_concurrent_files: int = 10
    thread_pool_workers: int = 4

    # 쉼표로 구분된 문자열을 리스트로 변환
    allowed_extensions: List[str] = [".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".json"]
    allowed_mime_types: List[str] = ["application/pdf", "text/plain", "application/json"]
    default_text_encoding: str = "utf-8"
    fallback_encodings: List[str] = ["utf-8", "cp949", "euc-kr", "latin1"]

    @classmethod
    @model_validator(mode='before')
    def parse_comma_separated_fields(cls, values):
        """쉼표로 구분된 문자열을 리스트로 변환"""
        comma_fields = ['allowed_extensions', 'allowed_mime_types', 'fallback_encodings']

        for field in comma_fields:
            if field in values and isinstance(values[field], str):
                values[field] = [x.strip() for x in values[field].split(',') if x.strip()]

        return values

    # 편의 프로퍼티들
    @property
    def allowed_extensions_set(self) -> Set[str]:
        """확장자를 소문자 set으로 반환"""
        return {ext.lower() for ext in self.allowed_extensions}

    @property
    def allowed_mime_types_set(self) -> Set[str]:
        """MIME 타입을 set으로 반환"""
        return set(self.allowed_mime_types)

    # ========================================
    # Ollama 설정
    # ========================================

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama 서버 URL"
    )
    ollama_embedding_model: str = Field(
        default="nomic-embed-text",
        description="임베딩 모델명"
    )
    ollama_timeout: int = Field(
        default=120,
        description="Ollama 타임아웃 (초)"
    )

    # ========================================
    # 벡터 DB 설정
    # ========================================

    # PostgreSQL 벡터 DB 설정
    vector_postgres_host: str = Field(
        default="localhost",
        description="벡터 DB PostgreSQL 호스트"
    )
    vector_postgres_port: int = Field(
        default=5432,
        description="벡터 DB PostgreSQL 포트"
    )
    vector_postgres_db: str = Field(
        default="vectordb",
        description="벡터 DB 데이터베이스명"
    )
    vector_postgres_user: str = Field(
        default="postgres",
        description="벡터 DB 사용자명"
    )
    vector_postgres_password: str = Field(
        default="password",
        description="벡터 DB 비밀번호"
    )

    # 벡터 DB 연결 설정
    vector_db_echo: bool = Field(
        default=False,
        description="벡터 DB SQL 쿼리 로깅"
    )
    vector_connection_pool_size: int = Field(
        default=5,
        description="벡터 DB 연결 풀 크기"
    )
    vector_max_overflow: int = Field(
        default=10,
        description="벡터 DB 최대 오버플로우 연결"
    )
    vector_pool_timeout: int = Field(
        default=30,
        description="벡터 DB 연결 풀 타임아웃"
    )

    # 텍스트 분할 기본 설정
    default_chunk_size: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="기본 텍스트 청크 크기"
    )
    default_chunk_overlap: int = Field(
        default=200,
        ge=0,
        le=1000,
        description="기본 텍스트 청크 겹침"
    )

    # 검색 기본 설정
    default_search_k: int = Field(
        default=5,
        ge=1,
        le=100,
        description="기본 검색 결과 수"
    )
    max_search_k: int = Field(
        default=50,
        ge=1,
        le=100,
        description="최대 검색 결과 수"
    )

    # 컬렉션 설정
    default_collection_name: str = Field(
        default="documents",
        description="기본 컬렉션명"
    )

    # 성능 설정
    vector_batch_size: int = Field(
        default=100,
        description="벡터 배치 처리 크기"
    )
    embedding_cache_size: int = Field(
        default=1000,
        description="임베딩 캐시 크기"
    )

    # 벡터 검색 고급 설정
    enable_vector_search: bool = Field(
        default=True,
        description="벡터 검색 기능 활성화"
    )
    vector_search_timeout: int = Field(
        default=30,
        description="벡터 검색 타임아웃 (초)"
    )

    @property
    def vector_connection_string(self) -> str:
        """벡터 DB 연결 문자열 (동기)"""
        return (
            f"postgresql://{self.vector_postgres_user}:"
            f"{self.vector_postgres_password}@{self.vector_postgres_host}:"
            f"{self.vector_postgres_port}/{self.vector_postgres_db}"
        )

    @property
    def vector_async_connection_string(self) -> str:
        """벡터 DB 비동기 연결 문자열"""
        return (
            f"postgresql+asyncpg://{self.vector_postgres_user}:"
            f"{self.vector_postgres_password}@{self.vector_postgres_host}:"
            f"{self.vector_postgres_port}/{self.vector_postgres_db}"
        )

    class Config:
        # 환경에 따라 동적으로 .env 파일 선택
        env_file = get_env_file()
        env_file_encoding = "utf-8"
        # 환경변수 이름 변환 (SNAKE_CASE)
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """환경변수 기반 설정 반환 (캐시됨)"""
    # 환경 설정 먼저 로드
    env = get_environment()

    # 환경별 기본값 설정
    defaults = {
        "environment": env,
        "debug": env.is_debug,
        "host": env.default_host,
        "log_level": env.default_log_level
    }

    # 환경변수로 오버라이드된 값들과 병합
    return Settings(**defaults)
