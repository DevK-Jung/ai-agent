"""RAG Agent 노드 — process_rag_agent 실행 후 supervisor로 복귀"""
from typing import Literal

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agents.constants import WorkflowSteps
from app.agents.state import RouterState
from app.agents.workflows.rag_workflow import process_rag_agent


async def rag_agent_node(state: RouterState) -> Command[Literal["supervisor"]]:
    messages = state.get("messages", [])

    # 마지막 HumanMessage를 original_query로 사용
    original_query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            original_query = msg.content
            break

    result = await process_rag_agent(
        messages=messages,
        original_query=original_query,
        user_id=state.get("user_id"),
    )

    return Command(
        update={
            "rag_context": result.get("answer", ""),
            "messages": [HumanMessage(content=result.get("answer", ""), name="rag_agent")],
        },
        goto=WorkflowSteps.SUPERVISOR,
    )
