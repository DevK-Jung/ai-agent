"""쿼리 재작성 노드

대화 이력을 보고 검색에 최적화된 쿼리로 재가공.
재시도 시에는 이전 rewritten_query를 확장.
retry_count를 여기서 증가.
"""
from pydantic import BaseModel

from app.agents.core.llm_provider import gpt4o_mini
from app.agents.prompts.rag import REWRITE_PROMPT
from app.agents.state import RAGState


class RewriteOutput(BaseModel):
    rewritten_query: str   # 벡터 검색용 재가공 쿼리
    keywords: list[str]    # pg_bigm 검색용 키워드 목록


_chain = REWRITE_PROMPT | gpt4o_mini.with_structured_output(RewriteOutput)


async def rewrite_node(state: RAGState) -> dict:
    result: RewriteOutput = await _chain.ainvoke({
        "messages": state["messages"],
        "current_query": state.get("rewritten_query") or state["original_query"],
        "attempt": state.get("retry_count", 0),
    })
    return {
        "rewritten_query": result.rewritten_query,
        "keywords": result.keywords,
        "retry_count": state.get("retry_count", 0) + 1,
    }
