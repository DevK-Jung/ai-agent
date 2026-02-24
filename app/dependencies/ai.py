"""
AI/임베딩 관련 의존성
"""
from threading import Lock
from typing import Optional

from app.infra.ai.embedding_service import BGEEmbeddingService


# Thread-safe 싱글톤 패턴
_embedding_service: Optional[BGEEmbeddingService] = None
_lock = Lock()


def get_embedding_service() -> BGEEmbeddingService:
    """
    임베딩 서비스 인스턴스를 반환합니다. (Thread-safe 싱글톤 패턴)
    
    Returns:
        BGEEmbeddingService: 임베딩 서비스 인스턴스
    """
    global _embedding_service
    if _embedding_service is None:
        with _lock:
            if _embedding_service is None:  # double-checked locking
                _embedding_service = BGEEmbeddingService()
    return _embedding_service


__all__ = ["get_embedding_service"]