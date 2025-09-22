from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.infra.ai.llm.llm_manager import LLMManager
from app.infra.ai.prompt.dependencies import PromptManagerDep


def get_llm_manager(settings: SettingsDep, prompt_manager: PromptManagerDep) -> LLMManager:
    return LLMManager(settings, prompt_manager)


LLMManagerDep = Annotated[LLMManager, Depends(get_llm_manager)]
