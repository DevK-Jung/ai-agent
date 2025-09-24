# infra/vector_db/dependencies.py
import asyncio
from typing import Annotated, Optional

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.infra.vector_db.client import VectorDBClient

# 전역 클라이언트 인스턴스
_vector_client: Optional[VectorDBClient] = None
_client_lock = asyncio.Lock()


async def get_vector_db_client(settings: SettingsDep) -> VectorDBClient:
    """초기화된 벡터DB 클라이언트 반환"""
    global _vector_client

    if _vector_client is None:
        async with _client_lock:
            if _vector_client is None:
                _vector_client = VectorDBClient(settings)
                await _vector_client.initialize()

    return _vector_client


VectorDBClientDep = Annotated[VectorDBClient, Depends(get_vector_db_client)]

async def get_vector_db_collection(settings: SettingsDep) -> VectorDBClient:
    """초기화된 벡터DB 클라이언트 반환"""
    global _vector_client

    if _vector_client is None:
        async with _client_lock:
            if _vector_client is None:
                _vector_client = VectorDBClient(settings)
                await _vector_client.initialize()

    return _vector_client


# 앱 생명주기 관리
async def startup_vector_db():
    """앱 시작시 벡터DB 초기화"""
    from app.core.config.settings import get_settings
    settings = get_settings()
    client = await get_vector_db_client(settings)
    # 미리 기본 벡터스토어 생성
    await client.get_vectorstore()


async def shutdown_vector_db():
    """앱 종료시 정리"""
    global _vector_client
    if _vector_client:
        await _vector_client.close()
        _vector_client = None
