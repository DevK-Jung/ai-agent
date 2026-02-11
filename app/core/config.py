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
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"


settings = Settings()