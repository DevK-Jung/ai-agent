from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.domains.llm.service import LLMService
from app.infra.ai.llm.dependencies import LLMManagerDep


def get_llm_service(
        settings: SettingsDep,
        llm_manager: LLMManagerDep
) -> LLMService:
    return LLMService(settings, llm_manager)


# Dependency annotations
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
