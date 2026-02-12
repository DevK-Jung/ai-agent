import os
from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    # Server
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # Agent Node Models
    CLASSIFIER_MODEL: str = "gpt-4o-mini"
    CLASSIFIER_TEMPERATURE: float = 0.1
    GENERATOR_MODEL: str = "gpt-4o-mini"
    GENERATOR_TEMPERATURE: float = 0.7
    
    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_agent"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_EXTERNAL_PORT: int = 5433
    POSTGRES_INTERNAL_PORT: int = 5432
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_EXTERNAL_PORT}/{self.POSTGRES_DB}"
    
    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_EXTERNAL_PORT}/{self.POSTGRES_DB}"
    
    # File Upload Configuration
    ALLOWED_FILE_TYPES: str = "text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "data/uploads"
    
    # Text Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 100
    CHUNK_SEPARATORS: str = "\\n\\n,\\n,.,\\ ,"
    
    # Embedding Model Configuration
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSIONS: int = 1024
    
    @computed_field
    @property
    def ALLOWED_FILE_TYPES_LIST(self) -> list[str]:
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]
    
    @computed_field 
    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @computed_field
    @property
    def CHUNK_SEPARATORS_LIST(self) -> list[str]:
        """청킹 구분자들을 리스트로 변환 (이스케이프 처리)"""
        separators = [sep.strip() for sep in self.CHUNK_SEPARATORS.split(",")]
        # 이스케이프 문자 처리
        processed = []
        for sep in separators:
            sep = sep.replace("\\n", "\n")
            sep = sep.replace("\\ ", " ")
            if sep == "":
                sep = ""
            processed.append(sep)
        return processed
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"  # development, production
    
    class Config:
        env_file = ".env"


settings = Settings()