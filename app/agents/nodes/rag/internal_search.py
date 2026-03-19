"""내부 검색 노드

hybrid search (vector + pg_bigm + RRF) 호출.
"""
from app.agents.tools.internal_search import hybrid_search
from app.agents.state import RAGState


async def internal_search_node(state: RAGState) -> dict:
    context, citations = await hybrid_search(
        query=state["rewritten_query"],
        keywords=state["keywords"],
        user_id=state.get("user_id"),
    )
    return {
        "rag_context": context,
        "citations": citations,
        "search_source": "internal",
    }
