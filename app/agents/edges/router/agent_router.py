"""서브 에이전트 선택 라우터"""

from typing import Literal

from app.agents.constants import AgentTypes
from app.agents.state import RouterState


def select_agent(state: RouterState) -> Literal["chat_agent"]:
    """agent_type에 따라 서브 에이전트를 선택한다.

    새 에이전트 추가 시:
    1. AgentTypes에 상수 추가
    2. 반환 타입 Literal에 추가
    3. 아래 분기 추가
    4. router_workflow.py에 노드 등록
    """
    agent_type = state.get("agent_type", AgentTypes.CHAT)
    print(f"Agent Router: agent_type = {agent_type}")
    return f"{agent_type}_agent"
