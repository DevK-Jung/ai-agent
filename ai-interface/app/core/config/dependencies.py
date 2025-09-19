from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config.settings import get_settings, Settings


@lru_cache()
def get_settings_cached() -> Settings:
    """설정 싱글톤 인스턴스"""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_cached)]
