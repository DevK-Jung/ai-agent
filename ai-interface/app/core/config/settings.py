import os
from functools import lru_cache
from typing import Optional

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


class Settings(BaseSettings):
    # 기본 애플리케이션 설정
    app_name: str = "FastAPI Application"
    version: str = "1.0.0"

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
    def cors_origins(self) -> list[str]:
        """CORS 허용 오리진 리스트"""
        origins_str = os.getenv("ALLOWED_ORIGINS", self.allowed_origins)
        return [origin.strip() for origin in origins_str.split(",") if origin.strip()]

    # Redis 설정 (캐싱용)
    redis_url: Optional[str] = None

    # 외부 API 설정
    openai_api_key: Optional[str] = None

    # 파일 업로드 설정
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB

    # 로깅 설정
    log_level: str = "INFO"
    log_file: str = "app.log"

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
