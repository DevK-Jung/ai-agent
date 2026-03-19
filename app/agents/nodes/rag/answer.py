"""최종 답변 생성 노드

search_source에 따라 인용 포맷 분기:
- internal: 파일명 기반
- web: URL 기반
"""
from app.agents.core.llm_provider import gpt4o
from app.agents.prompts.rag import ANSWER_PROMPT
from app.agents.state import RAGState
from app.core.config import settings

_chain = ANSWER_PROMPT | gpt4o


async def answer_node(state: RAGState) -> dict:
    search_source = state.get("search_source", "internal")
    citations = state.get("citations", [])

    if search_source == "internal":
        citations_text = "\n".join(f"- {c}" for c in citations) or "없음"
    else:
        citations_text = "\n".join(f"- {c}" for c in citations) or "없음"

    response = await _chain.ainvoke({
        "messages": state["messages"],
        "rag_context": state.get("rag_context", ""),
        "citations": citations_text,
        "search_source": search_source,
    })

    return {
        "answer": response.content.strip(),
    }
