from typing import AsyncGenerator

from langchain_openai import ChatOpenAI

from app.agents.prompts.generation import (
    ERROR_MESSAGE
)
from app.agents.state import ChatState
from app.core.config import settings


def generate_answer(state: ChatState) -> ChatState:
    """답변을 생성하는 노드"""
    from langchain_core.messages import AIMessage

    llm = ChatOpenAI(
        model=settings.GENERATOR_MODEL,
        temperature=settings.GENERATOR_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY
    ).with_config(tags=["STREAM_GENERATOR"])

    # 메시지 히스토리 사용
    messages = state.get("messages", [])

    try:
        # 전체 메시지 히스토리를 사용하여 응답 생성
        response = llm.invoke(messages)
        answer = response.content.strip()

        # 응답을 메시지 히스토리에 추가
        messages.append(AIMessage(content=answer))

    except Exception as e:
        print(f"Answer generation error: {e}")
        answer = ERROR_MESSAGE
        messages.append(AIMessage(content=answer))

    # 상태 업데이트
    state["answer"] = answer
    state["model_used"] = settings.GENERATOR_MODEL
    state["messages"] = messages

    return state


async def generate_answer_stream(state: ChatState) -> AsyncGenerator[str, None]:
    """답변을 스트리밍으로 생성하는 함수"""

    llm = ChatOpenAI(
        model=settings.GENERATOR_MODEL,
        temperature=settings.GENERATOR_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
        streaming=True
    )

    # 전체 메시지 히스토리 사용
    messages = state.get("messages", [])

    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        print(f"Answer generation error: {e}")
        yield ERROR_MESSAGE
