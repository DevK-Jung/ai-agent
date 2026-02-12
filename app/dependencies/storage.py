"""
파일 저장 관련 의존성
"""
from functools import lru_cache
from app.infra.storage.file_storage import FileStorageService


@lru_cache()
def get_file_storage_service() -> FileStorageService:
    """FileStorageService 의존성 주입 (싱글톤)"""
    return FileStorageService()


__all__ = ["get_file_storage_service"]