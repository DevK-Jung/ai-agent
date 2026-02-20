from typing import Optional, List, Dict, Any
from typing_extensions import TypedDict

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
    context: Optional[str]
    is_new_session: Optional[bool]


class MeetingState(TypedDict):
    """회의록 에이전트 상태 정의"""
    audio_file_path: str
    transcript: List[Dict[str, Any]]  # WhisperX 결과 (타임스탬프 + 화자 포함)
    merged_transcript: str            # 화자 태깅된 텍스트로 변환
    minutes: str                      # 최종 회의록
    session_id: str
    user_id: str
