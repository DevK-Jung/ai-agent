from typing import Optional
import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 기본 애플리케이션 설정
    app_name: str = "FastAPI Application"
    version: str = "1.0.0"
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

    # CORS 설정
    allowed_origins: list = ["http://localhost:3000", "http://localhost:8080"]

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

    # 환경 구분
    environment: str = "development"

    class Config:
        # .env 파일에서 환경변수 읽기
        env_file = ".env"
        env_file_encoding = "utf-8"
        # 환경변수 이름 변환 (SNAKE_CASE)
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()


# 환경별 설정 클래스들
class DevelopmentSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///./dev.db"
    log_level: str = "DEBUG"


class ProductionSettings(Settings):
    debug: bool = False
    database_url: str  # 환경변수에서 반드시 설정되어야 함
    secret_key: str  # 환경변수에서 반드시 설정되어야 함
    log_level: str = "WARNING"


class TestingSettings(Settings):
    debug: bool = True
    database_url: str = "sqlite:///./test.db"
    log_level: str = "DEBUG"


def get_settings() -> Settings:
    """환경에 따라 적절한 설정을 반환"""
    environment = os.getenv("ENVIRONMENT", "development")

    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()