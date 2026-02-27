"""LLM 기반 Sub-Agent 감지 노드"""
import logging

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.agents.constants import AgentTypes
from app.agents.core.llm_provider import gpt4o_mini
from app.agents.prompts.router import AGENT_DETECTION_PROMPT
from app.agents.state import RouterState

logger = logging.getLogger(__name__)

_VALID_AGENT_TYPES = {AgentTypes.CHAT, AgentTypes.MEETING}

_detection_chain = AGENT_DETECTION_PROMPT | gpt4o_mini | StrOutputParser()


async def detect_agent(state: RouterState) -> dict:
    """사용자 메시지를 분석하여 처리할 서브 에이전트를 감지

    state.agent_type이 이미 설정된 경우 패스.
    없으면 LLM으로 인텐트 감지, 기본값은 chat.
    """
    # API에서 명시적으로 agent_type이 전달된 경우 패스
    existing_agent_type = state.get("agent_type")
    if existing_agent_type and existing_agent_type in _VALID_AGENT_TYPES:
        return {}

    messages = state.get("messages", [])
    last_human_message = next(
        (msg.content for msg in reversed(messages) if isinstance(msg, HumanMessage)),
        ""
    )

    if not last_human_message:
        return {"agent_type": AgentTypes.CHAT}

    try:
        agent_type = await _detection_chain.ainvoke({"user_message": last_human_message})
        agent_type = agent_type.strip().lower()

        if agent_type not in _VALID_AGENT_TYPES:
            agent_type = AgentTypes.CHAT

    except Exception as e:
        logger.error(f"Agent detection error: {e}")
        agent_type = AgentTypes.CHAT

    return {"agent_type": agent_type}
