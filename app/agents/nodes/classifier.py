# nodes/classify.py
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from app.agents.prompts.classification import (
    CLASSIFICATION_PROMPT,
    VALID_QUESTION_TYPES,
    DEFAULT_QUESTION_TYPE
)
from app.agents.state import ChatState
from app.core.config import settings

_classifier_llm = ChatOpenAI(
    model=settings.CLASSIFIER_MODEL,
    temperature=settings.CLASSIFIER_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY
)

# StrOutputParser로 바로 문자열 반환
_classify_chain = CLASSIFICATION_PROMPT | _classifier_llm | StrOutputParser()


async def classify_question(state: ChatState) -> dict:
    messages = state.get("messages", [])
    last_human_message = next(
        (msg.content for msg in reversed(messages) if isinstance(msg, HumanMessage)),
        ""
    )

    try:
        question_type = await _classify_chain.ainvoke({"user_message": last_human_message})
        question_type = question_type.strip().upper()

        if question_type not in VALID_QUESTION_TYPES:
            question_type = DEFAULT_QUESTION_TYPE

    except Exception as e:
        print(f"Classification error: {e}")
        question_type = DEFAULT_QUESTION_TYPE

    return {
        "question_type": question_type,
        "model_used": settings.CLASSIFIER_MODEL
    }
