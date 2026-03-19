"""RAG Sub-Agent 워크플로우 (CRAG — Corrective RAG)

흐름:
  START → rewrite → internal_search
  internal_search → [internal_relevance_edge]
      ├─ relevant    → answer → END
      ├─ rewrite     → rewrite (retry_count 증가)
      └─ web_search  → web_search → [web_relevance_edge]
                              ├─ relevant   → answer → END
                              └─ irrelevant → fallback → END
"""
from langgraph.graph import StateGraph, END

from app.agents.edges.rag.internal_relevance import internal_relevance_edge
from app.agents.edges.rag.web_relevance import web_relevance_edge
from app.agents.nodes.rag.answer import answer_node
from app.agents.nodes.rag.internal_search import internal_search_node
from app.agents.nodes.rag.rewrite import rewrite_node
from app.agents.nodes.rag.web_search import web_search_node
from app.agents.state import RAGState


async def _fallback_node(state: RAGState) -> dict:
    """웹 검색도 관련 없을 때 고정 응답 반환 (LLM 호출 없음)"""
    return {
        "answer": "관련 정보를 찾을 수 없습니다.",
        "search_source": "none",
        "citations": [],
    }


def create_rag_workflow():
    wf = StateGraph(RAGState)

    wf.add_node("rewrite", rewrite_node)
    wf.add_node("internal_search", internal_search_node)
    wf.add_node("web_search", web_search_node)
    wf.add_node("answer", answer_node)
    wf.add_node("fallback", _fallback_node)

    wf.set_entry_point("rewrite")
    wf.add_edge("rewrite", "internal_search")

    wf.add_conditional_edges(
        "internal_search",
        internal_relevance_edge,
        {
            "relevant":   "answer",
            "rewrite":    "rewrite",
            "web_search": "web_search",
        },
    )

    wf.add_conditional_edges(
        "web_search",
        web_relevance_edge,
        {
            "relevant":   "answer",
            "irrelevant": "fallback",
        },
    )

    wf.add_edge("answer", END)
    wf.add_edge("fallback", END)

    return wf.compile()


_rag_app = create_rag_workflow()


async def process_rag_agent(messages: list, original_query: str, user_id: str | None = None) -> dict:
    """RAG Sub-Agent 실행 진입점"""
    initial_state: RAGState = {
        "messages": messages,
        "original_query": original_query,
        "rewritten_query": "",
        "keywords": [],
        "rag_context": "",
        "citations": [],
        "search_source": "internal",
        "retry_count": 0,
        "user_id": user_id,
        "answer": None,
    }
    final_state = await _rag_app.ainvoke(initial_state)
    return {
        "answer": final_state.get("answer", "관련 정보를 찾을 수 없습니다."),
        "citations": final_state.get("citations", []),
        "search_source": final_state.get("search_source", "none"),
    }
