"""Supervisor 노드 - LLM이 매 턴마다 다음 에이전트를 결정

흐름:
  supervisor → Command(goto="chat_agent"|"meeting_agent"|"final_response_agent")
  각 에이전트 완료 후 → Command(goto="supervisor") 복귀
  supervisor (모두 완료 판단) → Command(goto="final_response_agent")
  final_response_agent → Command(goto=END)
"""

import logging
from typing import Literal

from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)
from langgraph.types import Command
from typing_extensions import TypedDict

from app.agents.constants import WorkflowSteps
from app.agents.core.llm_provider import gpt4o
from app.agents.prompts.router import SUPERVISOR_SYSTEM_PROMPT
from app.agents.state import RouterState
from app.core.config import settings

members = ["chat_agent", "meeting_agent"]
options = members + ["FINISH"]


class SupervisorRoute(TypedDict):
    """Worker to route to next. If no workers needed, route to FINISH."""
    next: Literal[*options]
    reasoning: str


_supervisor_llm = gpt4o.with_structured_output(SupervisorRoute)


async def supervisor_node(state: RouterState) -> Command[
    Literal[*members, "summarize_conversations", "final_response_agent"]]:
    messages = state.get("messages", [])

    # 토큰 초과 체크 (deterministic — LLM 불필요)
    if gpt4o.get_num_tokens_from_messages(messages) > settings.SUMMARIZE_MAX_TOKENS:
        return Command(goto=WorkflowSteps.SUMMARIZE_CONVERSATIONS)

    # LLM이 전체 messages를 보고 next 결정
    result: SupervisorRoute = await _supervisor_llm.ainvoke(
        [SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT)] + messages
    )

    goto = result["next"]
    logger.info("[supervisor] next=%s | reasoning=%s", goto, result["reasoning"])

    if goto == "FINISH":
        return Command(goto=WorkflowSteps.FINAL_RESPONSE_AGENT)

    return Command(goto=goto)
