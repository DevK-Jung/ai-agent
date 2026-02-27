"""최상위 Router Workflow

흐름:
  START → summarize → detect_agent
                          ↓ select_agent
                          └─ chat_agent → END

- 대화 이력: LangGraph PostgreSQL checkpointer가 thread_id 단위로 자동 관리
- 토큰 관리: 커스텀 summarize_node (70% 초과 시 요약 + 이전 메시지 삭제)
"""

import uuid
from typing import AsyncGenerator, Dict, Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START

from app.agents.constants import WorkflowSteps, StreamEventTypes, StreamMessages
from app.agents.nodes.router.detect_agent import detect_agent
from app.agents.nodes.router.summarize import summarize_node
from app.agents.edges.router.agent_router import select_agent
from app.agents.edges.router.token_router import route_check_token
from app.agents.state import RouterState
from app.agents.workflows.chat_workflow import create_chat_subgraph
from app.agents.workflows.meeting_workflow import create_meeting_subgraph
from app.core.config import settings


async def create_router_workflow():
    """최상위 Router Workflow 생성"""

    from app.agents.infra.checkpointer import get_postgres_checkpointer

    workflow = StateGraph(RouterState)

    # --- 노드 등록 ---
    workflow.add_node(WorkflowSteps.SUMMARIZE_CONVERSATIONS, summarize_node)
    workflow.add_node(WorkflowSteps.DETECT_AGENT, detect_agent)
    workflow.add_node(WorkflowSteps.CHAT_AGENT, create_chat_subgraph())
    workflow.add_node(WorkflowSteps.MEETING_AGENT, create_meeting_subgraph())

    # --- 엣지 연결 ---

    # START → [token check] → summarize or skip → detect_agent
    workflow.add_conditional_edges(
        START,
        route_check_token,
        {
            "summarize": WorkflowSteps.SUMMARIZE_CONVERSATIONS,
            "skip": WorkflowSteps.DETECT_AGENT,
        }
    )
    workflow.add_edge(WorkflowSteps.SUMMARIZE_CONVERSATIONS, WorkflowSteps.DETECT_AGENT)

    # detect_agent → 서브 에이전트 선택
    workflow.add_conditional_edges(
        WorkflowSteps.DETECT_AGENT,
        select_agent,
        {
            "chat_agent": WorkflowSteps.CHAT_AGENT,
            "meeting_agent": WorkflowSteps.MEETING_AGENT,
        }
    )

    # 서브 에이전트 완료 → END
    workflow.add_edge(WorkflowSteps.CHAT_AGENT, END)
    workflow.add_edge(WorkflowSteps.MEETING_AGENT, END)

    checkpointer_context = await get_postgres_checkpointer()
    return workflow, checkpointer_context


# =========================
# 일반 요청 처리
# =========================
async def process_chat(
        message: str,
        user_id: str | None = None,
        session_id: str | None = None,
        agent_type: str | None = None,
        audio_file_path: str | None = None,
) -> dict:
    if not session_id:
        session_id = str(uuid.uuid4())

    workflow, checkpointer_context = await create_router_workflow()

    try:
        async with checkpointer_context as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)

            config: RunnableConfig = {
                "configurable": {"thread_id": session_id}
            }

            initial_state: dict = {
                "messages": [HumanMessage(content=message)],
                "session_id": session_id,
                "user_id": user_id,
            }
            if agent_type:
                initial_state["agent_type"] = agent_type
            if audio_file_path:
                initial_state["audio_file_path"] = audio_file_path

            final_state = await app.ainvoke(initial_state, config=config)

            return {
                "answer": final_state.get("answer"),
                "session_id": session_id,
                "question_type": final_state.get("question_type"),
                "model_used": final_state.get("model_used"),
            }

    except Exception as e:
        print(f"Router workflow error: {e}")
        return {
            "answer": StreamMessages.PROCESSING_ERROR,
            "session_id": session_id,
            "question_type": None,
            "model_used": settings.GPT4O_MODEL,
        }


# =========================
# 스트리밍 처리
# =========================
async def process_chat_stream(
        message: str,
        user_id: str | None = None,
        session_id: str | None = None,
        agent_type: str | None = None,
        audio_file_path: str | None = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    if not session_id:
        session_id = str(uuid.uuid4())

    yield {
        "type": StreamEventTypes.START,
        "session_id": session_id,
        "message": StreamMessages.ANALYZING_QUESTION,
    }

    try:
        workflow, checkpointer_context = await create_router_workflow()

        async with checkpointer_context as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)

            config: RunnableConfig = {
                "configurable": {"thread_id": session_id}
            }

            initial_state: dict = {
                "messages": [HumanMessage(content=message)],
                "session_id": session_id,
                "user_id": user_id,
            }
            if agent_type:
                initial_state["agent_type"] = agent_type
            if audio_file_path:
                initial_state["audio_file_path"] = audio_file_path

            async for event in app.astream_events(
                    initial_state,
                    config=config,
                    version="v2",
            ):

                event_type = event["event"]
                event_name = event.get("name", "")
                event_data = event.get("data", {})
                tags = event.get("tags", [])

                # 요약 시작
                if event_type == "on_chain_start" and event_name == WorkflowSteps.SUMMARIZE_CONVERSATIONS:
                    yield {
                        "type": StreamEventTypes.PROGRESS,
                        "step": "summarizing",
                        "message": StreamMessages.SUMMARIZING_CONVERSATION,
                    }

                # 분류 완료
                elif event_type == "on_chain_end" and event_name == WorkflowSteps.CLASSIFIER:
                    output = event_data.get("output", {})
                    yield {
                        "type": StreamEventTypes.PROGRESS,
                        "step": "classified",
                        "question_type": output.get("question_type"),
                        "used_model": output.get("model_used"),
                        "message": StreamMessages.question_type_classified(
                            output.get("question_type", "알 수 없음")
                        ),
                    }

                # 답변 생성 시작
                elif event_type == "on_chain_start" and event_name == WorkflowSteps.GENERATOR:
                    yield {
                        "type": StreamEventTypes.PROGRESS,
                        "step": WorkflowSteps.GENERATOR,
                        "used_model": settings.GPT4O_MODEL,
                        "message": StreamMessages.GENERATING_ANSWER,
                    }

                # LLM 스트리밍 토큰
                elif event_type == "on_chat_model_stream" and "STREAM_GENERATOR" in tags:
                    chunk = event_data.get("chunk", {})
                    if hasattr(chunk, "content") and chunk.content:
                        yield {
                            "type": StreamEventTypes.CHUNK,
                            "chunk": chunk.content,
                            "session_id": session_id,
                        }

                # 답변 완료
                elif event_type == "on_chain_end" and event_name == WorkflowSteps.GENERATOR:
                    output = event_data.get("output", {})
                    yield {
                        "type": StreamEventTypes.COMPLETE,
                        "answer": output.get("answer"),
                        "session_id": session_id,
                        "question_type": output.get("question_type"),
                        "model_used": output.get("model_used"),
                    }

    except Exception as e:
        yield {
            "type": StreamEventTypes.ERROR,
            "session_id": session_id,
            "error": str(e),
            "message": StreamMessages.PROCESSING_ERROR,
        }
