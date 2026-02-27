"""중앙 LLM 인스턴스 관리

모든 노드는 여기서 export된 인스턴스를 import해서 사용.
특수 설정(tags, max_tokens 등)은 각 노드에서 .bind() / .with_config()로 처리.
"""

from langchain_openai import ChatOpenAI

from app.core.config import settings

gpt4o_mini = ChatOpenAI(
    model=settings.GPT4O_MINI_MODEL,
    temperature=settings.GPT4O_MINI_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
)

gpt4o = ChatOpenAI(
    model=settings.GPT4O_MODEL,
    temperature=settings.GPT4O_TEMPERATURE,
    api_key=settings.OPENAI_API_KEY,
)
