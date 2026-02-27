"""질문 분류 노드"""

from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from app.agents.prompts.chat import (
    CLASSIFICATION_PROMPT,
    VALID_QUESTION_TYPES,
    DEFAULT_QUESTION_TYPE,
)
from app.agents.state import RouterState
from app.core.config import settings
from app.agents.core.llm_provider import gpt4o_mini

_classify_chain = CLASSIFICATION_PROMPT | gpt4o_mini | StrOutputParser()


async def classify_question(state: RouterState) -> dict:
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
        "model_used": settings.GPT4O_MINI_MODEL
    }
