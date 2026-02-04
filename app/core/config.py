import os
from pydantic_settings import BaseSettings


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
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/ai_agent"
    
    # Vector Database
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()