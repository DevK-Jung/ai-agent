"""내부 검색 결과 관련성 판단 엣지

internal_search_node 직후 conditional edge.
LLM으로 관련성 판단 → relevant / rewrite / web_search 3-way 분기.
"""
from typing import Literal

from pydantic import BaseModel

from app.agents.core.llm_provider import gpt4o_mini
from app.agents.prompts.rag import INTERNAL_RELEVANCE_PROMPT
from app.agents.state import RAGState
from app.core.config import settings


class RelevanceOutput(BaseModel):
    relevance: Literal["relevant", "unrelevant"]


_chain = INTERNAL_RELEVANCE_PROMPT | gpt4o_mini.with_structured_output(RelevanceOutput)


async def internal_relevance_edge(
    state: RAGState,
) -> Literal["relevant", "rewrite", "web_search"]:
    """
    내부 검색 결과 관련성 판단.
    - relevant            → answer_node
    - unrelevant + retry < MAX → rewrite_node (재시도)
    - unrelevant + retry >= MAX → web_search_node
    """
    # 검색 결과 자체가 없으면 LLM 호출 생략
    if not state.get("rag_context"):
        if state.get("retry_count", 0) >= settings.RAG_MAX_RETRIES:
            return "web_search"
        return "rewrite"

    result: RelevanceOutput = await _chain.ainvoke({
        "query": state["original_query"],
        "context": state["rag_context"],
    })

    if result.relevance == "relevant":
        return "relevant"

    if state.get("retry_count", 0) >= settings.RAG_MAX_RETRIES:
        return "web_search"

    return "rewrite"
