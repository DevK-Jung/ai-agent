from typing import TypedDict, Optional


class ChatState(TypedDict):
    """LangGraph 상태 정의"""
    user_message: str
    user_id: Optional[str]
    session_id: Optional[str]
    question_type: Optional[str]
    answer: Optional[str]
    model_used: str