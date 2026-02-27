"""Chat Sub-Agent 내부 라우터 - 질문 타입 기반 분기"""

from typing import Literal

from app.agents.state import RouterState


async def route_question(state: RouterState) -> Literal["generator", "search_generator", "summary_generator", "compare_generator"]:
    """질문 타입에 따라 처리 경로를 결정하는 라우터"""

    question_type = state.get("question_type", "FACT")
    print(f"Chat Router: question_type = {question_type}")

    if question_type == "FACT":
        return "generator"
    elif question_type == "SUMMARY":
        return "summary_generator"
    elif question_type == "COMPARE":
        return "compare_generator"
    elif question_type == "EVIDENCE":
        return "search_generator"
    else:
        return "generator"
