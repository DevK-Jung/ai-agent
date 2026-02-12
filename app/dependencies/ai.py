"""
AI/임베딩 관련 의존성
"""
from functools import lru_cache
from app.infra.ai.embedding_service import get_embedding_service


@lru_cache()
def get_embedding_service_cached():
    """EmbeddingService 의존성 주입 (싱글톤)"""
    return get_embedding_service()


__all__ = ["get_embedding_service_cached"]