"""답변 생성 노드"""

from langchain_core.messages import AIMessage

from app.agents.prompts.chat import PROMPT_MAP, ERROR_MESSAGE
from app.agents.state import RouterState
from app.core.config import settings
from app.agents.core.llm_provider import gpt4o

# 스트리밍 태그 부착 (astream_events에서 "STREAM_GENERATOR" 필터링용)
_generator_llm = gpt4o.with_config(tags=["STREAM_GENERATOR"])


async def generate_answer(state: RouterState) -> dict:
    """답변을 생성하는 노드"""
    messages_for_llm = state.get("messages", [])
    question_type = state.get("question_type", "FACT")
    rag_context = state.get("rag_context", "")

    prompt = PROMPT_MAP.get(question_type, PROMPT_MAP["FACT"])
    chain = prompt | _generator_llm

    try:
        response = await chain.ainvoke({
            "messages": messages_for_llm,
            "context": rag_context
        })
        answer = response.content.strip()

    except Exception as e:
        print(f"Answer generation error: {e}")
        answer = ERROR_MESSAGE

    return {
        "answer": answer,
        "model_used": settings.GPT4O_MODEL,
        "messages": [AIMessage(content=answer)]
    }
