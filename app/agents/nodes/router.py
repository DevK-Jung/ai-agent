from typing import Literal

from app.agents.state import ChatState
from app.agents.constants import WorkflowSteps


async def route_question(state: ChatState) -> Literal["generator", "search_generator", "summary_generator", "compare_generator"]:
    """질문 타입에 따라 처리 경로를 결정하는 라우터 노드"""
    
    question_type = state.get("question_type", "FACT")
    print(f"Router: question_type = {question_type}")
    
    # 질문 타입별 라우팅 로직
    if question_type == "FACT":
        print("Router: routing to 'generator'")
        return "generator"  # WorkflowSteps.GENERATOR 대신 직접 문자열 사용
    elif question_type == "SUMMARY":
        print("Router: routing to 'summary_generator'")
        return "summary_generator"  # 향후 요약 전용 노드
    elif question_type == "COMPARE":
        print("Router: routing to 'compare_generator'")
        return "compare_generator"  # 향후 비교 전용 노드
    elif question_type == "EVIDENCE":
        print("Router: routing to 'search_generator'")
        return "search_generator"   # 향후 검색 강화 노드
    else:
        # 기본값
        print("Router: routing to 'generator' (default)")
        return "generator"  # WorkflowSteps.GENERATOR 대신 직접 문자열 사용