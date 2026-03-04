"""Chat Sub-Agent 서브그래프"""

from app.agents.nodes.chat.classifier import classify_question
from app.agents.nodes.chat.generator import generate_answer
from app.agents.state import RouterState


async def process_chat_agent(state: RouterState) -> dict:
    """Chat Sub-Agent 실행 함수"""
    classify_result = await classify_question(state)

    merged_state = {**state, **classify_result}
    generate_result = await generate_answer(merged_state)

    return {
        "answer": generate_result.get("answer", ""),
        "question_type": classify_result.get("question_type"),
        "model_used": generate_result.get("model_used"),
    }
