from typing import Literal

from app.agents.state import ChatState
from app.agents.constants import WorkflowSteps


def route_question(state: ChatState) -> Literal["generator", "search_generator", "summary_generator", "compare_generator"]:
    """질문 타입에 따라 처리 경로를 결정하는 라우터 노드"""
    
    question_type = state.get("question_type", "FACT")
    
    # 질문 타입별 라우팅 로직
    if question_type == "FACT":
        return WorkflowSteps.GENERATOR
    elif question_type == "SUMMARY":
        return "summary_generator"  # 향후 요약 전용 노드
    elif question_type == "COMPARE":
        return "compare_generator"  # 향후 비교 전용 노드
    elif question_type == "EVIDENCE":
        return "search_generator"   # 향후 검색 강화 노드
    else:
        # 기본값
        return WorkflowSteps.GENERATOR