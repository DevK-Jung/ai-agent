from typing import Optional
from langgraph.graph import MessagesState


class ChatState(MessagesState):
    """LangGraph 상태 정의 - 메시지 히스토리 포함"""
    user_id: Optional[str]
    session_id: Optional[str]
    thread_id: Optional[str]
    question_type: Optional[str]
    answer: Optional[str]
    model_used: str
    summary: Optional[str]  # 이전 대화 요약