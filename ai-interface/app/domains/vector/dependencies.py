# app/domains/vector/dependencies.py
import logging
from contextlib import asynccontextmanager
from typing import Optional

from app.domains.vector.service import VectorService

from app.core.config.settings import get_settings
from app.core.database.vector_connection import VectorConnectionManager
from app.domains.vector.repository import VectorRepository

logger = logging.getLogger(__name__)

# 도메인 전용 전역 인스턴스들
_vector_connection_manager: Optional[VectorConnectionManager] = None
_vector_repository: Optional[VectorRepository] = None
_vector_service: Optional[VectorService] = None


async def get_vector_connection_manager() -> VectorConnectionManager:
    """벡터 연결 관리자 반환 (싱글톤)"""
    global _vector_connection_manager

    if _vector_connection_manager is None:
        settings = get_settings()
        _vector_connection_manager = VectorConnectionManager(settings)
        await _vector_connection_manager.initialize()
        logger.info("벡터 연결 관리자 초기화 완료")

    return _vector_connection_manager


async def get_vector_repository() -> VectorRepository:
    """벡터 리포지토리 반환 (싱글톤)"""
    global _vector_repository

    if _vector_repository is None:
        connection_manager = await get_vector_connection_manager()
        _vector_repository = VectorRepository(connection_manager)
        logger.info("벡터 리포지토리 초기화 완료")

    return _vector_repository


async def get_vector_service() -> VectorService:
    """벡터 서비스 인스턴스 반환 (싱글톤, 비동기)"""
    global _vector_service

    if _vector_service is None:
        settings = get_settings()
        repository = await get_vector_repository()
        _vector_service = VectorService(repository, settings)
        logger.info("벡터 서비스 초기화 완료")

    return _vector_service


@asynccontextmanager
async def vector_service_context():
    """벡터 서비스 컨텍스트 매니저"""
    service = await get_vector_service()
    try:
        yield service
    finally:
        # 필요시 정리 작업
        pass


@asynccontextmanager
async def vector_repository_context():
    """벡터 리포지토리 컨텍스트 매니저"""
    repository = await get_vector_repository()
    try:
        yield repository
    finally:
        # 필요시 정리 작업
        pass


# 연결 테스트 및 헬스체크
async def test_vector_connections():
    """모든 벡터 관련 연결 테스트"""
    try:
        connection_manager = await get_vector_connection_manager()
        test_results = await connection_manager.test_connection()
        return test_results
    except Exception as e:
        logger.error(f"벡터 연결 테스트 실패: {e}")
        return {"overall": False, "error": str(e)}


async def health_check_vector():
    """벡터 도메인 헬스체크"""
    try:
        service = await get_vector_service()
        status = await service.get_status()

        return {
            "status": "healthy" if status.get("is_connected") else "unhealthy",
            "details": status
        }
    except Exception as e:
        logger.error(f"벡터 헬스체크 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# 도메인 정리 함수
async def cleanup_vector_domain():
    """벡터 도메인 리소스 정리"""
    global _vector_connection_manager, _vector_repository, _vector_service

    try:
        if _vector_repository:
            await _vector_repository.close()

        if _vector_connection_manager:
            await _vector_connection_manager.close()

        # 전역 변수 초기화
        _vector_connection_manager = None
        _vector_repository = None
        _vector_service = None

        logger.info("벡터 도메인 리소스 정리 완료")

    except Exception as e:
        logger.error(f"벡터 도메인 정리 실패: {e}")


# FastAPI 의존성 함수들 (Depends에서 사용)
def get_vector_service_dependency():
    """FastAPI Depends용 벡터 서비스 의존성"""

    async def _get_service():
        return await get_vector_service()

    return _get_service


def get_vector_repository_dependency():
    """FastAPI Depends용 벡터 리포지토리 의존성"""

    async def _get_repository():
        return await get_vector_repository()

    return _get_repository