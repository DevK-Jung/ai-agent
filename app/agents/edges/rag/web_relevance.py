"""웹 검색 결과 관련성 판단 엣지

web_search_node 직후 conditional edge.
관련 없으면 fallback_node로 → END. hallucination 방지.
"""
from typing import Literal

from pydantic import BaseModel

from app.agents.core.llm_provider import gpt4o_mini
from app.agents.prompts.rag import WEB_RELEVANCE_PROMPT
from app.agents.state import RAGState


class WebRelevanceOutput(BaseModel):
    relevance: Literal["relevant", "irrelevant"]


_chain = WEB_RELEVANCE_PROMPT | gpt4o_mini.with_structured_output(WebRelevanceOutput)


async def web_relevance_edge(
    state: RAGState,
) -> Literal["relevant", "irrelevant"]:
    """
    웹 검색 결과 관련성 판단.
    - relevant   → answer_node
    - irrelevant → fallback_node (END)
    """
    if not state.get("rag_context"):
        return "irrelevant"

    result: WebRelevanceOutput = await _chain.ainvoke({
        "query": state["original_query"],
        "context": state["rag_context"],
    })
    return result.relevance
