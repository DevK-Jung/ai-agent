"""Chat Agent 노드 - process_chat_agent를 실행 후 supervisor로 복귀"""
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.constants import WorkflowSteps
from app.agents.state import RouterState
from app.agents.workflows.chat_workflow import process_chat_agent


async def chat_agent_node(state: RouterState) -> Command[Literal["supervisor"]]:
    result = await process_chat_agent(state)

    return Command(
        update={
            "question_type": result.get("question_type"),
            "model_used": result.get("model_used"),
            "messages": [HumanMessage(content=result.get("answer", ""), name="chat_agent")],
        },
        goto=WorkflowSteps.SUPERVISOR,
    )
