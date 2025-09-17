"""
로깅 설정 구성
"""

from typing import Dict, Any
import sys

from app.core.config.settings import get_settings

settings = get_settings()


def get_logging_config() -> Dict[str, Any]:
    """환경별 로깅 설정 반환"""

    formatters = {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "()": "app.core.utils.logging.formatters.JsonFormatter",
        },
        "colored": {
            "()": "app.core.utils.logging.formatters.ColoredFormatter",
        }
    }

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO" if settings.debug else "WARNING",
            "formatter": "colored" if settings.debug else "default",
            "stream": sys.stdout
        },
        "file_info": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "data/logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "file_error": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "data/logs/error.log",
            "maxBytes": 10485760,
            "backupCount": 5,
            "encoding": "utf8"
        }
    }

    loggers = {
        "app": {
            "level": "DEBUG" if settings.debug else "INFO",
            "handlers": ["console", "file_info", "file_error"],
            "propagate": False
        },
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": loggers,
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }