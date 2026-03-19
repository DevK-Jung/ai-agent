from typing import Optional, List, Dict, Any, Literal

from langgraph.graph import MessagesState
from typing_extensions import TypedDict


class RouterState(MessagesState):
    """LangGraph 최상위 Router 상태 정의"""
    user_id: Optional[str]
    session_id: Optional[str]
    thread_id: Optional[str]
    agent_type: Optional[str]  # "chat" | "meeting" | ...
    answer: Optional[str]
    model_used: str
    question_type: Optional[str]
    rag_context: Optional[str]  # RAG 검색 결과
    audio_file_path: Optional[str]  # Meeting Agent 오디오 파일 경로


# 하위 호환성 유지
ChatState = RouterState


class RAGState(MessagesState):
    """CRAG (Corrective RAG) Sub-Agent 상태 정의

    """
    original_query: str  # 원본 사용자 질문
    rewritten_query: str  # 벡터 검색용 재정의 쿼리
    keywords: List[str]  # pg_bigm용 키워드 목록
    rag_context: str  # 검색 결과 컨텍스트
    citations: List[str]  # 인용 출처 (내부: 파일명, 웹: URL)
    search_source: Literal["internal", "web", "none"]  # 검색 출처
    retry_count: int  # 내부 검색 재시도 횟수
    user_id: Optional[str]
    answer: Optional[str]


class MeetingState(TypedDict):
    """회의록 에이전트 상태 정의"""
    audio_file_path: str
    transcript: List[Dict[str, Any]]
    merged_transcript: str
    minutes: str
    session_id: str
    user_id: str
