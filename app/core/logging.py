"""
로깅 설정 모듈
"""
import logging
import logging.config
from typing import Dict, Any

from app.core.config import settings


def get_logging_config() -> Dict[str, Any]:
    """로깅 설정 딕셔너리를 반환합니다."""
    
    # 환경에 따른 핸들러 설정
    handlers = ["console"]
    app_handlers = ["console"]
    
    # 운영환경에서만 파일 핸들러 추가
    if settings.ENVIRONMENT == "production":
        handlers.append("file")
        app_handlers.append("file")
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            # 애플리케이션 로거
            "app": {
                "level": "DEBUG",
                "handlers": app_handlers,
                "propagate": False,
            },
            # FastAPI/Uvicorn 로거
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            # SQLAlchemy 로거
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": handlers,
        },
    }
    
    # 운영환경에서만 파일 핸들러 설정 추가
    if settings.ENVIRONMENT == "production":
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        }
    
    return config


def setup_logging() -> None:
    """로깅 설정을 초기화합니다."""
    import os
    
    # 운영환경에서만 로그 디렉토리 생성
    if settings.ENVIRONMENT == "production":
        os.makedirs("logs", exist_ok=True)
    
    # 로깅 설정 적용
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # 설정 완료 로그
    logger = logging.getLogger("app.core.logging")
    logger.info(f"로깅 설정 완료 - 환경: {settings.ENVIRONMENT}, 레벨: {settings.LOG_LEVEL}")


def get_logger(name: str) -> logging.Logger:
    """애플리케이션 로거를 반환합니다."""
    return logging.getLogger(f"app.{name}")