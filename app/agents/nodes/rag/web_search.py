"""웹 검색 노드

내부 검색 MAX_RETRIES 회 실패 시 호출.
OpenAI built-in web search (gpt-4o-mini) 사용.
"""
import logging

from openai import AsyncOpenAI, APIError
from openai.types.responses import WebSearchToolParam

from app.agents.state import RAGState
from app.core.config import settings

logger = logging.getLogger(__name__)

_openai: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _openai
    if _openai is None:
        _openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai


async def web_search_node(state: RAGState) -> dict:
    try:
        client = get_openai_client()
        resp = await client.responses.create(
            model="gpt-4o-mini",
            tools=[
                WebSearchToolParam(
                    type="web_search",
                    search_context_size="medium",
                )
            ],
            input=state["rewritten_query"],
        )

        citations: list[dict] = []
        for block in getattr(resp, "output", []):
            for item in getattr(block, "content", []):
                for ref in getattr(item, "annotations", []):
                    if getattr(ref, "type", None) == "url_citation":
                        url = getattr(ref, "url", None)
                        title = getattr(ref, "title", "")
                        if url and url not in [c["url"] for c in citations]:
                            citations.append({"url": url, "title": title})

        return {
            "rag_context": resp.output_text,
            "citations": citations,
            "search_source": "web",
        }

    except APIError as e:
        logger.error(f"Web search API error: {e}")
        return {
            "rag_context": "",
            "citations": [],
            "search_source": "web_failed",
        }
