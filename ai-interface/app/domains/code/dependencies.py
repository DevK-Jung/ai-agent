# app/domains/code/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.domains.code.service import CodeService
from app.domains.llm.dependencies import LLMServiceDep
from app.infra.code.dependencies import CodeExecutorDep


def get_code_service(
        code_executor: CodeExecutorDep,
        llm_service: LLMServiceDep,
        settings: SettingsDep
) -> CodeService:
    return CodeService(code_executor, llm_service, settings)


CodeServiceDep = Annotated[CodeService, Depends(get_code_service)]
