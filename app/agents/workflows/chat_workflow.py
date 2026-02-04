from langgraph.graph import StateGraph, END
from app.agents.state import ChatState
from app.agents.nodes.classifier import classify_question
from app.agents.nodes.generator import generate_answer
import uuid


def create_chat_workflow():
    """채팅 워크플로우를 생성합니다."""
    
    # StateGraph 생성
    workflow = StateGraph(ChatState)
    
    # 노드 추가
    workflow.add_node("classifier", classify_question)
    workflow.add_node("generator", generate_answer)
    
    # 엣지 설정
    workflow.set_entry_point("classifier")
    workflow.add_edge("classifier", "generator")
    workflow.add_edge("generator", END)
    
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
            "answer": "죄송합니다. 처리 중 오류가 발생했습니다.",
            "session_id": session_id,
            "question_type": None,
            "model_used": "gpt-4o-mini"
        }