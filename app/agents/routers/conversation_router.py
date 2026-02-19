"""대화 이력 복원이 필요한지 판단하는 라우터"""

from typing import Literal
from langchain_core.runnables import RunnableConfig
from app.agents.state import ChatState


def need_prev_conversation(state: ChatState) -> Literal["load_db", "check_token"]:
    """세션 상태에 따른 분기 판단"""
    
    messages = state.get("messages", [])
    session_id = state.get("session_id")
    
    # checkpointer가 복원했으면 이미 메시지 여러 개
    if len(messages) > 1:
        return "check_token"
    
    # session_id가 없으면 새 대화 - DB 조회 불필요
    if not session_id:
        return "check_token"
    
    # 기존 세션이지만 checkpointer에 없음 = DB 조회 필요  
    return "load_db"