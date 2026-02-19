import uuid
from typing import AsyncGenerator, Dict, Any

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END

from app.agents.constants import WorkflowSteps, StreamEventTypes, StreamMessages
from app.agents.nodes.classifier import classify_question
from app.agents.nodes.generator import generate_answer
from app.agents.nodes.router import route_question
from app.agents.state import ChatState
from app.core.config import settings


async def create_chat_workflow():
    """채팅 워크플로우 생성"""

    from app.agents.infra.checkpointer import get_postgres_checkpointer

    workflow = StateGraph(ChatState)

    workflow.add_node(WorkflowSteps.CLASSIFIER, classify_question)
    workflow.add_node(WorkflowSteps.ROUTER, route_question)
    workflow.add_node(WorkflowSteps.GENERATOR, generate_answer)

    workflow.set_entry_point(WorkflowSteps.CLASSIFIER)
    workflow.add_edge(WorkflowSteps.CLASSIFIER, WorkflowSteps.ROUTER)
    workflow.add_conditional_edges(
        WorkflowSteps.ROUTER,
        route_question,
        {
            WorkflowSteps.GENERATOR: WorkflowSteps.GENERATOR,
            "search_generator": WorkflowSteps.GENERATOR,  # 임시로 기본 generator 사용
            "summary_generator": WorkflowSteps.GENERATOR,  # 임시로 기본 generator 사용
            "compare_generator": WorkflowSteps.GENERATOR,  # 임시로 기본 generator 사용
        }
    )
    workflow.add_edge(WorkflowSteps.GENERATOR, END)

    checkpointer_context = await get_postgres_checkpointer()
    return workflow, checkpointer_context


# =========================
# 일반 요청 처리
# =========================
async def process_chat(
        message: str,
        user_id: str | None = None,
        session_id: str | None = None,
) -> dict:
    # 세션 없으면 새로 생성
    if not session_id:
        session_id = str(uuid.uuid4())

    workflow, checkpointer_context = await create_chat_workflow()

    try:
        async with checkpointer_context as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)

            config: RunnableConfig = {
                "configurable": {"thread_id": session_id}
            }

            final_state = await app.ainvoke(
                {"messages": [HumanMessage(content=message)]},
                config=config,
            )

            return {
                "answer": final_state.get("answer"),
                "session_id": session_id,
                "question_type": final_state.get("question_type"),
                "model_used": final_state.get("model_used"),
            }

    except Exception as e:
        print(f"Workflow error: {e}")
        return {
            "answer": StreamMessages.PROCESSING_ERROR,
            "session_id": session_id,
            "question_type": None,
            "model_used": settings.GENERATOR_MODEL,
        }


# =========================
# 스트리밍 처리
# =========================
async def process_chat_stream(
        message: str,
        user_id: str | None = None,
        session_id: str | None = None,
) -> AsyncGenerator[Dict[str, Any], None]:
    if not session_id:
        session_id = str(uuid.uuid4())

    yield {
        "type": StreamEventTypes.START,
        "session_id": session_id,
        "message": StreamMessages.ANALYZING_QUESTION,
    }

    try:
        workflow, checkpointer_context = await create_chat_workflow()

        async with checkpointer_context as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)

            config: RunnableConfig = {
                "configurable": {"thread_id": session_id}
            }

            async for event in app.astream_events(
                    {"messages": [HumanMessage(content=message)]},
                    config=config,
                    version="v2",
            ):

                event_type = event["event"]
                event_name = event.get("name", "")
                event_data = event.get("data", {})
                tags = event.get("tags", [])

                # 분류 완료
                if event_type == "on_chain_end" and event_name == WorkflowSteps.CLASSIFIER:
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
                
                # 라우팅 완료
                elif event_type == "on_chain_end" and event_name == WorkflowSteps.ROUTER:
                    yield {
                        "type": StreamEventTypes.PROGRESS,
                        "step": "routed",
                        "message": "적절한 처리 경로를 선택했습니다...",
                    }

                # 답변 생성 시작
                elif event_type == "on_chain_start" and event_name == WorkflowSteps.GENERATOR:
                    yield {
                        "type": StreamEventTypes.PROGRESS,
                        "step": WorkflowSteps.GENERATOR,
                        "used_model": settings.GENERATOR_MODEL,
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
