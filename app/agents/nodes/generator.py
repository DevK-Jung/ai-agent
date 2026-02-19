from typing import AsyncGenerator

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.agents.prompts.generation import ERROR_MESSAGE
from app.agents.state import ChatState
from app.core.config import settings


async def generate_answer(state: ChatState) -> dict:
    """답변을 생성하는 노드"""
    print("Generator: Starting generate_answer")

    llm = ChatOpenAI(
        model=settings.GENERATOR_MODEL,
        temperature=settings.GENERATOR_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY
    ).with_config(tags=["STREAM_GENERATOR"])

    messages = state.get("messages", [])
    print(f"Generator: Got {len(messages)} messages")

    try:
        response = llm.invoke(messages)
        answer = response.content.strip()
        messages.append(AIMessage(content=answer))

    except Exception as e:
        print(f"Answer generation error: {e}")
        answer = ERROR_MESSAGE
        messages.append(AIMessage(content=answer))

    return {
        "answer": answer,
        "model_used": settings.GENERATOR_MODEL,
        "messages": messages,
    }


async def generate_answer_stream(state: ChatState) -> AsyncGenerator[str, None]:
    """답변을 스트리밍으로 생성하는 함수"""

    llm = ChatOpenAI(
        model=settings.GENERATOR_MODEL,
        temperature=settings.GENERATOR_TEMPERATURE,
        api_key=settings.OPENAI_API_KEY,
        streaming=True
    )

    messages = state.get("messages", [])

    try:
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content
    except Exception as e:
        print(f"Answer generation error: {e}")
        yield ERROR_MESSAGE