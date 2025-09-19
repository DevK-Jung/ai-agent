# app/infra/code/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.domains.code.service import CodeService
from app.infra.code.dependencies import CodeExecutorDep


def get_code_service(
        code_executor: CodeExecutorDep,
        settings: SettingsDep
) -> CodeService:
    return CodeService(code_executor, settings)


CodeServiceDep = Annotated[CodeService, Depends(get_code_service)]
