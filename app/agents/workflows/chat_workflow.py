from langgraph.graph import StateGraph, END
from app.agents.state import ChatState
from app.agents.nodes.classifier import classify_question
from app.agents.nodes.generator import generate_answer
from app.agents.constants import WorkflowSteps, StreamEventTypes, StreamMessages
from typing import AsyncGenerator, Dict, Any
import uuid


def create_chat_workflow():
    """채팅 워크플로우를 생성합니다."""
    
    # StateGraph 생성
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node(WorkflowSteps.CLASSIFIER, classify_question)
    workflow.add_node(WorkflowSteps.GENERATOR, generate_answer)
    
    # 엣지 설정
    workflow.set_entry_point(WorkflowSteps.CLASSIFIER)
    workflow.add_edge(WorkflowSteps.CLASSIFIER, WorkflowSteps.GENERATOR)
    workflow.add_edge(WorkflowSteps.GENERATOR, END)
    
    # 워크플로우 컴파일
    app = workflow.compile()
    
    return app


async def process_chat(message: str, user_id: str = None, session_id: str = None) -> dict:
    """채팅 메시지를 처리합니다."""
    
    # 세션 ID가 없으면 새로 생성
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 초기 상태 설정
    initial_state: ChatState = {
        "user_message": message,
        "user_id": user_id,
        "session_id": session_id,
        "question_type": None,
        "answer": None,
        "model_used": "gpt-4o-mini"
    }
    
    # 워크플로우 실행
    app = create_chat_workflow()
    
    try:
        # 상태를 통해 워크플로우 실행
        final_state = app.invoke(initial_state)
        
        return {
            "answer": final_state["answer"],
            "session_id": final_state["session_id"],
            "question_type": final_state["question_type"],
            "model_used": final_state["model_used"]
        }
    except Exception as e:
        print(f"Workflow error: {e}")
        return {
            "answer": StreamMessages.PROCESSING_ERROR,
            "session_id": session_id,
            "question_type": None,
            "model_used": "gpt-4o-mini"
        }


async def process_chat_stream(message: str, user_id: str = None, session_id: str = None) -> AsyncGenerator[Dict[str, Any], None]:
    """채팅 메시지를 스트리밍으로 처리합니다."""
    
    # 세션 ID가 없으면 새로 생성
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # 시작 이벤트 전송
    yield {
        "type": StreamEventTypes.START,
        "session_id": session_id,
        "message": StreamMessages.ANALYZING_QUESTION
    }
    
    # 초기 상태 설정
    initial_state: ChatState = {
        "user_message": message,
        "user_id": user_id,
        "session_id": session_id,
        "question_type": None,
        "answer": None,
        "model_used": "gpt-4o-mini"
    }
    
    try:
        # 워크플로우 실행
        app = create_chat_workflow()
        
        # astream_events로 세밀한 이벤트 추적
        async for event in app.astream_events(initial_state, version="v2"):
            event_type = event["event"]
            event_name = event.get("name", "")
            event_data = event.get("data", {})
            tags = event.get("tags", [])
            
            # 분류 노드 완료 시
            if event_type == "on_chain_end" and event_name == WorkflowSteps.CLASSIFIER:
                output = event_data.get("output", {})
                yield {
                    "type": StreamEventTypes.PROGRESS,
                    "step": "classified",
                    "question_type": output.get("question_type"),
                    "message": StreamMessages.question_type_classified(output.get("question_type", "알 수 없음"))
                }
            
            # 답변 생성 시작 시
            elif event_type == "on_chain_start" and event_name == WorkflowSteps.GENERATOR:
                yield {
                    "type": StreamEventTypes.PROGRESS,
                    "step": WorkflowSteps.GENERATOR,
                    "message": StreamMessages.GENERATING_ANSWER
                }
            
            # LLM 스트리밍 토큰 (STREAM_GENERATOR 태그가 있는 경우만)
            elif event_type == "on_chat_model_stream" and "STREAM_GENERATOR" in tags:
                chunk = event_data.get("chunk", {})
                if hasattr(chunk, 'content') and chunk.content:
                    yield {
                        "type": StreamEventTypes.CHUNK,
                        "chunk": chunk.content,
                        "session_id": session_id
                    }
            
            # 답변 생성 완료 시
            elif event_type == "on_chain_end" and event_name == WorkflowSteps.GENERATOR:
                output = event_data.get("output", {})
                yield {
                    "type": StreamEventTypes.COMPLETE,
                    "answer": output.get("answer"),
                    "session_id": output.get("session_id"),
                    "question_type": output.get("question_type"),
                    "model_used": output.get("model_used")
                }
        
    except Exception as e:
        # 오류 발생 시 에러 정보 전송
        yield {
            "type": StreamEventTypes.ERROR,
            "session_id": session_id,
            "error": str(e),
            "message": StreamMessages.PROCESSING_ERROR
        }