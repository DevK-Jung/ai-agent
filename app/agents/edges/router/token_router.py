"""토큰 초과 여부에 따라 summarize 또는 skip으로 분기하는 엣지"""

from typing import Literal

from app.agents.core.llm_provider import gpt4o
from app.agents.state import RouterState
from app.core.config import settings


def route_check_token(state: RouterState) -> Literal["summarize", "skip"]:
    messages = state.get("messages", [])
    token_count = gpt4o.get_num_tokens_from_messages(messages)
    return "summarize" if token_count > settings.SUMMARIZE_MAX_TOKENS else "skip"