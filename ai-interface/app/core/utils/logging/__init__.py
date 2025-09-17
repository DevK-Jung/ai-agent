"""
로깅 설정 메인 모듈
"""

from .config import get_logging_config
from .helpers import get_logger, log_request, log_response, log_ai_request
import logging.config
from pathlib import Path


def setup_logging():
    """애플리케이션 로깅 설정"""
    # 로그 디렉토리 생성
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # 로깅 설정 적용
    logging_config = get_logging_config()
    logging.config.dictConfig(logging_config)

    # 시작 로그
    logger = get_logger("app")
    logger.info("로깅 설정 완료")
    logger.info(f"로그 디렉토리: {log_dir.absolute()}")


__all__ = [
    "setup_logging",
    "get_logger",
    "log_request",
    "log_response",
    "log_ai_request"
]