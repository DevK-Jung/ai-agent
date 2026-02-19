from langchain_openai import ChatOpenAI

from app.agents.state import ChatState
from app.core.config import settings
from app.agents.prompts.classification import (
    VALID_QUESTION_TYPES,
    DEFAULT_QUESTION_TYPE
)


def classify_question(state: ChatState) -> dict:
    """사용자 질문을 분류하는 노드"""

    llm = ChatOpenAI(
        model=settings.CLASSIFIER_MODEL,
        temperature=settings.CLASSIFIER_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY
    )

    # 전체 메시지 히스토리 사용
    messages = state.get("messages", [])

    try:
        response = llm.invoke(messages)
        question_type = response.content.strip().upper()

        # 유효한 분류인지 확인
        if question_type not in VALID_QUESTION_TYPES:
            question_type = DEFAULT_QUESTION_TYPE

    except Exception as e:
        print(f"Classification error: {e}")
        question_type = DEFAULT_QUESTION_TYPE

    # dict 반환
    return {
        "question_type": question_type,
        "model_used": settings.CLASSIFIER_MODEL
    }
