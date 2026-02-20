# nodes/generation.py
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.prompts.generation import PROMPT_MAP, ERROR_MESSAGE
from app.agents.state import ChatState
from app.core.config import settings

_generator_llm = ChatOpenAI(
    model=settings.GENERATOR_MODEL,
    temperature=settings.GENERATOR_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
    tags=["STREAM_GENERATOR"]
)


async def generate_answer(state: ChatState) -> dict:
    """답변을 생성하는 노드"""

    messages = state.get("messages", [])
    question_type = state.get("question_type", "FACT")
    context = state.get("context", "")  # RAG 검색 결과

    # 질문 유형에 맞는 프롬프트 선택
    prompt = PROMPT_MAP.get(question_type, PROMPT_MAP["FACT"])
    chain = prompt | _generator_llm

    try:
        response = await chain.ainvoke({
            "messages": messages,
            "context": context
        })
        answer = response.content.strip()

    except Exception as e:
        print(f"Answer generation error: {e}")
        answer = ERROR_MESSAGE

    return {
        "answer": answer,
        "model_used": settings.GENERATOR_MODEL,
        "messages": [AIMessage(content=answer)]
    }
