from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.core.database.vector_connection import VectorConnectionManager


@lru_cache()
def get_vector_connection_manager_cached(settings: SettingsDep) -> VectorConnectionManager:
    """벡터 연결 관리자 싱글톤 인스턴스"""
    return VectorConnectionManager(settings)


VectorConnectionManagerDep = Annotated[VectorConnectionManager, Depends(get_vector_connection_manager_cached)]