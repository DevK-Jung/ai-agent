import os
from pydantic_settings import BaseSettings
from pydantic import computed_field


class Settings(BaseSettings):
    # Server
    PORT: int = 8080
    HOST: str = "0.0.0.0"
    
    # OpenAI
    OPENAI_API_KEY: str = ""
    
    # LlamaCloud
    LLAMA_CLOUD_API_KEY: str = ""
    
    # Agent Node Models
    CLASSIFIER_MODEL: str = "gpt-4o-mini"
    CLASSIFIER_TEMPERATURE: float = 0.1
    GENERATOR_MODEL: str = "gpt-4o"
    GENERATOR_TEMPERATURE: float = 0.7
    CONVERSATION_SUMMARY_MODEL: str = "gpt-4o-mini"
    CONVERSATION_SUMMARY_TEMPERATURE: float = 0.1
    
    # Meeting Agent Models
    MINUTES_MODEL: str = "gpt-4o"
    MINUTES_TEMPERATURE: float = 0.3
    
    # WhisperX Configuration
    HF_TOKEN: str = ""  # HuggingFace token for speaker diarization
    WHISPERX_MODEL: str = "large-v2"  # Whisper model size
    WHISPERX_DEVICE: str = "cpu"  # "cuda" or "cpu" 
    WHISPERX_LANGUAGE: str = "ko"  # Default language code
    WHISPERX_BATCH_SIZE: int = 16  # Batch size for transcription
    WHISPERX_SAMPLE_RATE: int = 16000  # Audio sample rate
    WHISPERX_MAX_DURATION_MINUTES: int = 120  # Max audio duration (2 hours)
    WHISPERX_LONG_AUDIO_THRESHOLD_MINUTES: int = 30  # Long audio threshold (30 minutes)
    WHISPERX_CHUNK_DURATION_MINUTES: int = 10  # Chunk duration for long audio (10 minutes)
    
    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "ai_agent"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_EXTERNAL_PORT: int = 5433
    POSTGRES_INTERNAL_PORT: int = 5432
    
    # Database Connection Pool Configuration
    DB_POOL_SIZE: int = 10
    DB_POOL_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_PRE_PING: bool = True
    
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_EXTERNAL_PORT}/{self.POSTGRES_DB}"
    
    @computed_field
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_EXTERNAL_PORT}/{self.POSTGRES_DB}"
    
    @computed_field
    @property
    def CHECKPOINTER_CONNECTION_STRING(self) -> str:
        """체크포인터용 연결 문자열"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_EXTERNAL_PORT}"
            f"/{self.POSTGRES_DB}"
        )
    
    # File Upload Configuration
    ALLOWED_FILE_TYPES: str = "text/plain,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "data/uploads"
    
    # Text Chunking Configuration (Token-based)
    CHUNK_SIZE: int = 512  # 토큰 단위
    CHUNK_OVERLAP: int = 50  # 토큰 단위
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
    
    # Checkpointer Configuration
    CHECKPOINTER_SCHEMA: str = "public"
    CHECKPOINTER_APP_NAME: str = "ai-agent-checkpointer"
    CHECKPOINTER_CONNECT_TIMEOUT: int = 10
    CHECKPOINTER_STATEMENT_TIMEOUT: int = 30000
    CHECKPOINTER_TTL_SECONDS: int = 3600  # 1시간 TTL
    
    # Logging
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"  # development, production
    
    class Config:
        env_file = ".env"


settings = Settings()