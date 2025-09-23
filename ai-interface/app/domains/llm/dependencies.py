from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.domains.file.dependencies import FileServiceDep
from app.domains.llm.service import LLMService
from app.infra.ai.llm.dependencies import LLMManagerDep


def get_llm_service(
        settings: SettingsDep,
        llm_manager: LLMManagerDep,
        file_service: FileServiceDep,
) -> LLMService:
    return LLMService(settings, llm_manager, file_service)


# Dependency annotations
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
