from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict

from langgraph.graph import MessagesState


class RouterState(MessagesState):
    """LangGraph 최상위 Router 상태 정의"""
    user_id: Optional[str]
    session_id: Optional[str]
    thread_id: Optional[str]
    agent_type: Optional[str]           # "chat" | "meeting" | ...
    answer: Optional[str]
    model_used: str
    question_type: Optional[str]
    rag_context: Optional[str]          # RAG 검색 결과
    audio_file_path: Optional[str]      # Meeting Agent 오디오 파일 경로


# 하위 호환성 유지
ChatState = RouterState


class MeetingState(TypedDict):
    """회의록 에이전트 상태 정의"""
    audio_file_path: str
    transcript: List[Dict[str, Any]]
    merged_transcript: str
    minutes: str
    session_id: str
    user_id: str
