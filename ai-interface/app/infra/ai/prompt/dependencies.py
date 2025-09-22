from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.infra.ai.prompt.prompt_manager import PromptManager


@lru_cache()
def get_prompt_manager() -> PromptManager:
    return PromptManager()


PromptManagerDep = Annotated[PromptManager, Depends(get_prompt_manager)]
