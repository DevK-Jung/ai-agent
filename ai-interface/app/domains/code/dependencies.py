# app/domains/code/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.domains.code.service import CodeService
from app.infra.code.dependencies import CodeExecutorDep
from app.infra.ai.code.code_generator import CodeGenerator
from app.infra.ai.llm.dependencies import LLMManagerDep
from app.infra.ai.prompt.dependencies import PromptManagerDep


def get_code_generator(
        llm_manager: LLMManagerDep,
        prompt_manager: PromptManagerDep,
        settings: SettingsDep
) -> CodeGenerator:
    return CodeGenerator(llm_manager, prompt_manager, settings)


def get_code_service(
        code_executor: CodeExecutorDep,
        code_generator: Annotated[CodeGenerator, Depends(get_code_generator)],
        settings: SettingsDep
) -> CodeService:
    return CodeService(code_executor, code_generator, settings)


CodeServiceDep = Annotated[CodeService, Depends(get_code_service)]
