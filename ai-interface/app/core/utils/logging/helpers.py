"""
로깅 헬퍼 함수들
"""

import logging


def get_logger(name: str = "app") -> logging.Logger:
    """로거 인스턴스 반환"""
    return logging.getLogger(name)


def log_request(request_id: str, method: str, url: str, user_id: str = None):
    """HTTP 요청 로깅"""
    logger = get_logger("app.access")
    extra = {
        "request_id": request_id,
        "endpoint": f"{method} {url}"
    }
    if user_id:
        extra["user_id"] = user_id

    logger.info(f"Request: {method} {url}", extra=extra)


def log_response(request_id: str, status_code: int, processing_time: float):
    """HTTP 응답 로깅"""
    logger = get_logger("app.access")
    extra = {
        "request_id": request_id,
        "status_code": status_code,
        "processing_time": processing_time
    }

    logger.info(
        f"Response: {status_code} ({processing_time:.3f}s)",
        extra=extra
    )


def log_ai_request(model: str, tokens_used: int, processing_time: float):
    """AI 요청 로깅"""
    logger = get_logger("app.ai")
    extra = {
        "model": model,
        "tokens_used": tokens_used,
        "processing_time": processing_time
    }

    logger.info(
        f"AI Request: {model} - {tokens_used} tokens ({processing_time:.3f}s)",
        extra=extra
    )