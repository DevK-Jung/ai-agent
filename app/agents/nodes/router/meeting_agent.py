"""Meeting Agent 노드 - process_meeting을 실행 후 supervisor로 복귀"""
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.constants import WorkflowSteps
from app.agents.state import RouterState
from app.agents.workflows.meeting_workflow import process_meeting


async def meeting_agent_node(state: RouterState) -> Command[Literal["supervisor"]]:
    result = await process_meeting(
        state.get("audio_file_path", ""),
        state.get("user_id"),
        state.get("session_id"),
    )
    return Command(
        update={
            "messages": [HumanMessage(content=result.get("minutes", "회의록 생성 실패"), name="meeting_agent")],
        },
        goto=WorkflowSteps.SUPERVISOR,
    )
