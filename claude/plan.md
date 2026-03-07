# Plan: RAG SubAgent (Tool-based) with Hybrid Search (pg_bigm + Vector + RRF) + OpenAI Web Search

## Context

내부 문서 기반 응답 생성을 위한 **별도 RAG SubAgent**를 구현.
- 에이전트에게 **tool 2개**를 부여: 사내문서 검색 tool + OpenAI 웹검색 tool
- 하이브리드 검색은 **pg_bigm 유사도 검색 + 벡터 검색 → RRF** 로 구현 (FTS 제외)
- 기존 chat_agent와 분리된 **독립적인 rag_workflow** 생성
- Supervisor가 내부 문서 관련 질문을 `rag_agent`로 라우팅

---

## 목표 아키텍처

```
supervisor
  └─ rag_agent_node
        ↓
   rag_workflow (LangGraph StateGraph)

   ┌─ query_rewriter_node  LLM: 대화 이력 기반 쿼리 재정의 + 키워드 추출
   │         ↓
   ├─ retriever_node        internal_search_tool 호출 (벡터 + pg_bigm + RRF)
   │         ↓
   ├─ relevance_judge_node  LLM: 검색 결과 관련성 판단
   │         ├─ relevant  → answer_generator_node
   │         └─ not relevant + retry < MAX → query_rewriter_node (재시도)
   │         └─ not relevant + retry >= MAX → answer_generator_node (best effort)
   │
   └─ answer_generator_node  LLM + web_search_tool (내부 문서 부족 시 보충)
        ↓
   → supervisor 복귀
```

---

## 현재 상태

| 항목 | 상태 | 파일 |
|------|------|------|
| 벡터 검색 | ✅ 구현됨 (미연결) | `search_repository.py` |
| pg_bigm 유사도 검색 | ❌ 미설치 | Docker 설정 필요 |
| RRF | ❌ 없음 | - |
| RAG workflow | ❌ 없음 | - |
| rag_agent_node | ❌ 없음 | - |
| OpenAI web search | ❌ 미연동 | - |

---

## 단계별 구현 계획

---

### Step 1: pg_bigm Docker 설정

**목표**: PostgreSQL 컨테이너에 pg_bigm 확장 추가

**수정 파일**: `docker/docker-compose.infra.yml`

pg_bigm이 내장된 커스텀 이미지 또는 init script 방식 사용:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16  # 현재 이미지 유지
    # pg_bigm은 shared_preload_libraries 없이도 CREATE EXTENSION으로 설치 가능
    # 단, pg_bigm 바이너리가 이미지에 포함되어야 함
```

**방법**: `docker/init/01_extensions.sql` 초기화 스크립트 추가

```sql
-- pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- pg_bigm (한국어 포함 CJK 전문검색)
CREATE EXTENSION IF NOT EXISTS pg_bigm;
```

> pg_bigm이 기본 이미지에 없을 경우 커스텀 Dockerfile 작성:
> ```dockerfile
> FROM pgvector/pgvector:pg16
> RUN apt-get update && apt-get install -y postgresql-16-pg-bigm
> ```

---

### Step 2: DocumentChunk 모델에 bigm 인덱스 추가

**수정 파일**: `app/models/document.py`

```python
from sqlalchemy import Index, text
from sqlalchemy.dialects.postgresql import TSVECTOR

class DocumentChunk(Base):
    ...
    # 기존 필드 유지
    content: Mapped[str]

    # bigm 인덱스는 별도 DDL로 생성 (SQLAlchemy Index로 표현)
    __table_args__ = (
        # 기존 인덱스들 유지...
        # pg_bigm GIN 인덱스 (content 컬럼에 직접 적용)
        Index(
            "ix_document_chunks_content_bigm",
            "content",
            postgresql_using="gin",
            postgresql_ops={"content": "gin_bigm_ops"},
        ),
    )
```

> pg_bigm은 별도 tsvector 컬럼 불필요.
> `content` 컬럼에 `gin_bigm_ops` 연산자 클래스로 GIN 인덱스 직접 생성.

### Step 3: config.py에 RAG 설정값 추가

**수정 파일**: `app/core/config.py`

```python
class Settings(BaseSettings):
    ...
    # RAG Self-Retriever 설정
    RAG_SEARCH_LIMIT: int = 10    # 각 검색 방식별 후보 수
    RAG_TOP_K: int = 5            # 최종 반환 개수
    RAG_RRF_K: int = 60           # RRF 상수 (Cormack et al. 2009)
    RAG_MAX_RETRIES: int = 3      # 관련성 없을 때 최대 재검색 횟수
```

---

### Step 4: 사내문서 검색 Tool (순수 Hybrid Search만)

**새 파일**: `app/agents/tools/internal_search.py`

tool은 검색만 담당. rewrite/judge는 workflow 노드에서 처리.

```python
import asyncio
from collections import defaultdict
from langchain_core.tools import tool
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.database import get_async_session
from app.models.document import Document, DocumentChunk
from app.infra.ai.embedding_service import embedding_service


async def _vector_search(session: AsyncSession, embedding: list[float], uid: str | None) -> list[dict]:
    """pgvector 코사인 유사도 검색"""
    stmt = (
        select(DocumentChunk)
        .join(Document)
        .where(Document.status == "completed")
        .order_by(DocumentChunk.embedding.cosine_distance(embedding))
        .limit(settings.RAG_SEARCH_LIMIT)
    )
    if uid:
        stmt = stmt.where(Document.user_id == uid)
    rows = (await session.execute(stmt)).scalars().all()
    return [{"id": str(r.id), "content": r.content} for r in rows]


async def _bigm_search(session: AsyncSession, keywords: str, uid: str | None) -> list[dict]:
    """pg_bigm GIN 인덱스 기반 bigram 유사도 검색"""
    stmt = (
        select(
            DocumentChunk,
            func.similarity(DocumentChunk.content, keywords).label("bigm_score"),
        )
        .join(Document)
        .where(
            DocumentChunk.content.op("%")(keywords),  # pg_bigm % 연산자
            Document.status == "completed",
        )
        .order_by(desc("bigm_score"))
        .limit(settings.RAG_SEARCH_LIMIT)
    )
    if uid:
        stmt = stmt.where(Document.user_id == uid)
    rows = (await session.execute(stmt)).all()
    return [{"id": str(r.DocumentChunk.id), "content": r.DocumentChunk.content} for r in rows]


def _rrf(result_lists: list[list[dict]]) -> list[dict]:
    """Reciprocal Rank Fusion: RRF(d) = Σ 1 / (k + rank(d))"""
    k = settings.RAG_RRF_K
    scores: dict[str, float] = defaultdict(float)
    data: dict[str, dict] = {}
    for result_list in result_lists:
        for rank, chunk in enumerate(result_list, start=1):
            cid = chunk["id"]
            scores[cid] += 1.0 / (k + rank)
            data[cid] = chunk
    return sorted(
        [{**data[cid], "rrf_score": scores[cid]} for cid in scores],
        key=lambda x: x["rrf_score"],
        reverse=True,
    )


@tool
async def internal_search_tool(query: str, keywords: str, user_id: str = "") -> str:
    """
    사내 내부 문서를 하이브리드 검색합니다.
    - query: 벡터 검색용 자연어 쿼리 (의미 기반)
    - keywords: pg_bigm 검색용 핵심 키워드 (공백 구분)

    Args:
        query: 벡터 검색에 사용할 자연어 질문
        keywords: pg_bigm 검색에 사용할 핵심 키워드 (공백 구분)
        user_id: 사용자 ID (문서 권한 필터링, 선택)
    """
    uid = user_id or None
    embedding = await embedding_service.get_embedding(query)

    async with get_async_session() as session:
        vector_results, bigm_results = await asyncio.gather(
            _vector_search(session, embedding, uid),
            _bigm_search(session, keywords, uid),
        )

    top = _rrf([vector_results, bigm_results])[: settings.RAG_TOP_K]

    if not top:
        return "관련 내부 문서를 찾을 수 없습니다."

    return "\n\n".join(
        f"[문서 {i}] (관련도: {r['rrf_score']:.3f})\n{r['content']}"
        for i, r in enumerate(top, 1)
    )
```

---

### Step 5: OpenAI Web Search Tool

**새 파일**: `app/agents/tools/openai_web_search.py`

```python
from langchain_core.tools import tool
from openai import AsyncOpenAI
from app.core.config import settings

_openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

@tool
async def web_search_tool(query: str) -> str:
    """
    인터넷 웹 검색을 수행합니다.
    사내 내부 문서에서 충분한 정보를 찾지 못했을 때 보충 정보를 검색하세요.

    Args:
        query: 검색할 질문 또는 키워드
    """
    resp = await _openai.responses.create(
        model="gpt-4o-mini-search-preview",
        tools=[{"type": "web_search_preview"}],
        input=query,
    )
    return resp.output_text
```

---

### Step 6: RAG State 정의

**수정 파일**: `app/agents/state.py`

```python
from typing import TypedDict, Optional, Annotated
from langgraph.graph import MessagesState

class RAGState(TypedDict):
    """RAG Workflow 전용 상태"""
    messages: list                    # 대화 이력 (RouterState에서 전달)
    original_query: str               # 원본 사용자 질문
    rewritten_query: str              # 벡터 검색용 재정의 쿼리
    keywords: str                     # pg_bigm용 키워드
    rag_context: str                  # 검색 결과 컨텍스트
    is_relevant: bool                 # 관련성 판단 결과
    retry_count: int                  # 현재 재시도 횟수
    user_id: Optional[str]
    answer: Optional[str]
```

---

### Step 7: RAG Workflow 노드들

**새 디렉토리**: `app/agents/nodes/rag/`

#### `query_rewriter.py`

```python
from app.agents.core.llm_provider import gpt4o_mini

_rewrite_chain = QUERY_REWRITE_PROMPT | gpt4o_mini | JsonOutputParser()

async def query_rewriter_node(state: RAGState) -> dict:
    """
    대화 이력과 원본 질문을 기반으로 검색 쿼리 재정의 + 키워드 추출.
    첫 실행: 원본 질문 기반. 재시도: 이전 쿼리 기반으로 확장.
    """
    result = await _rewrite_chain.ainvoke({
        "messages": state["messages"],
        "current_query": state.get("rewritten_query") or state["original_query"],
        "attempt": state.get("retry_count", 0),
    })
    return {
        "rewritten_query": result["rewritten_query"],
        "keywords": result["keywords"],
    }
```

#### `retriever.py`

```python
async def retriever_node(state: RAGState) -> dict:
    """internal_search_tool 호출하여 hybrid search 수행"""
    result = await internal_search_tool.ainvoke({
        "query": state["rewritten_query"],
        "keywords": state["keywords"],
        "user_id": state.get("user_id", ""),
    })
    return {"rag_context": result}
```

#### `relevance_judge.py`

```python
_judge_chain = RELEVANCE_JUDGE_PROMPT | gpt4o_mini | StrOutputParser()

async def relevance_judge_node(state: RAGState) -> dict:
    """검색 결과가 원본 질문과 관련 있는지 LLM으로 판단"""
    result = await _judge_chain.ainvoke({
        "query": state["original_query"],
        "context": state["rag_context"][:1000],  # 미리보기만 전달
    })
    return {"is_relevant": result.strip().upper() == "YES"}


def route_after_judge(state: RAGState) -> str:
    """관련성 판단 결과 + 재시도 횟수에 따라 다음 노드 결정"""
    if state["is_relevant"]:
        return "answer_generator"
    if state.get("retry_count", 0) < settings.RAG_MAX_RETRIES - 1:
        return "query_rewriter"   # 재시도
    return "answer_generator"     # 한계 도달 → best effort
```

#### `answer_generator.py`

```python
_answer_llm = gpt4o.bind_tools([web_search_tool])

async def answer_generator_node(state: RAGState) -> dict:
    """
    RAG 컨텍스트 기반 답변 생성.
    내부 문서 컨텍스트가 부족하면 LLM이 web_search_tool을 자율 호출.
    """
    response = await (ANSWER_PROMPT | _answer_llm).ainvoke({
        "messages": state["messages"],
        "context": state["rag_context"],
    })
    return {"answer": response.content}
```

---

### Step 8: RAG Workflow 조립

**새 파일**: `app/agents/workflows/rag_workflow.py`

```python
from langgraph.graph import StateGraph, END
from app.agents.state import RAGState
from app.agents.nodes.rag.query_rewriter import query_rewriter_node
from app.agents.nodes.rag.retriever import retriever_node
from app.agents.nodes.rag.relevance_judge import relevance_judge_node, route_after_judge
from app.agents.nodes.rag.answer_generator import answer_generator_node

def create_rag_workflow():
    workflow = StateGraph(RAGState)

    workflow.add_node("query_rewriter", query_rewriter_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("relevance_judge", relevance_judge_node)
    workflow.add_node("answer_generator", answer_generator_node)

    workflow.set_entry_point("query_rewriter")
    workflow.add_edge("query_rewriter", "retriever")
    workflow.add_edge("retriever", "relevance_judge")
    workflow.add_conditional_edges(
        "relevance_judge",
        route_after_judge,
        {
            "query_rewriter": "query_rewriter",   # 재시도
            "answer_generator": "answer_generator",
        },
    )
    workflow.add_edge("answer_generator", END)

    return workflow.compile()

_rag_app = create_rag_workflow()


async def process_rag_agent(state: RouterState) -> dict:
    messages = state.get("messages", [])
    last_human = next(
        (m.content for m in reversed(messages) if isinstance(m, HumanMessage)), ""
    )

    result = await _rag_app.ainvoke({
        "messages": messages,
        "original_query": last_human,
        "rewritten_query": "",
        "keywords": "",
        "rag_context": "",
        "is_relevant": False,
        "retry_count": 0,
        "user_id": state.get("user_id"),
        "answer": None,
    })
    return {
        "answer": result.get("answer", ""),
        "model_used": settings.GPT4O_MODEL,
    }
```

---

### Step 9: Router에 rag_agent_node 추가

**새 파일**: `app/agents/nodes/router/rag_agent.py`

```python
from langgraph.types import Command

async def rag_agent_node(state: RouterState) -> Command[Literal["supervisor"]]:
    """RAG SubAgent 노드 - 사내 문서 검색 후 답변 생성"""
    result = await process_rag_agent(state)

    return Command(
        update={
            "answer": result.get("answer"),
            "model_used": result.get("model_used"),
            "messages": [
                HumanMessage(content=result.get("answer", ""), name="rag_agent")
            ],
        },
        goto=WorkflowSteps.SUPERVISOR,
    )
```

**수정 파일**: `app/agents/workflows/router_workflow.py`

```python
workflow.add_node(WorkflowSteps.RAG_AGENT, rag_agent_node)  # 추가
```

---

### Step 10: Supervisor 업데이트

**수정 파일**: `app/agents/nodes/router/supervisor.py`

```python
# SupervisorRoute members에 rag_agent 추가
members = ["chat_agent", "meeting_agent", "rag_agent"]

# SUPERVISOR_SYSTEM_PROMPT에 rag_agent 설명 추가
"""
- rag_agent: 사내 내부 문서 기반 Q&A. 정책, 제품 스펙, 내부 보고서 등 내부 문서 관련 질문
- chat_agent: 일반 대화 및 문서와 무관한 질문
- meeting_agent: 회의록 생성 (오디오 파일 처리)
"""
```

**수정 파일**: `app/agents/constants.py`

```python
class WorkflowSteps:
    ...
    RAG_AGENT = "rag_agent"  # 추가
```

---

## 파일 변경 요약

| 작업 | 파일 | 변경 유형 |
|------|------|----------|
| pg_bigm Docker 설정 | `docker/docker-compose.infra.yml` 또는 `docker/Dockerfile.postgres` | 수정/신규 |
| DB 초기화 스크립트 | `docker/init/01_extensions.sql` | 신규 |
| bigm GIN 인덱스 | `app/models/document.py` | 수정 |
| RAG 설정값 (SEARCH_LIMIT, TOP_K, RRF_K, MAX_RETRIES) | `app/core/config.py` | 수정 |
| 사내문서 검색 tool (순수 Hybrid Search) | `app/agents/tools/internal_search.py` | **신규** |
| OpenAI 웹검색 tool | `app/agents/tools/openai_web_search.py` | **신규** |
| RAG State | `app/agents/state.py` | 수정 |
| query_rewriter_node | `app/agents/nodes/rag/query_rewriter.py` | **신규** |
| retriever_node | `app/agents/nodes/rag/retriever.py` | **신규** |
| relevance_judge_node + edge | `app/agents/nodes/rag/relevance_judge.py` | **신규** |
| answer_generator_node | `app/agents/nodes/rag/answer_generator.py` | **신규** |
| RAG workflow (StateGraph) | `app/agents/workflows/rag_workflow.py` | **신규** |
| RAG 프롬프트 | `app/agents/prompts/rag.py` | **신규** |
| rag_agent_node | `app/agents/nodes/router/rag_agent.py` | **신규** |
| Router 노드 등록 | `app/agents/workflows/router_workflow.py` | 수정 |
| Supervisor 라우팅 | `app/agents/nodes/router/supervisor.py` | 수정 |
| 상수 추가 | `app/agents/constants.py` | 수정 |

---

## 검증 방법

```bash
# 1. pg_bigm 설치 확인
# psql: SELECT * FROM pg_extension WHERE extname = 'pg_bigm';

# 2. bigm 인덱스 확인
# psql: \d document_chunks  (ix_document_chunks_content_bigm 인덱스 존재 확인)

# 3. 하이브리드 검색 단위 테스트
python -m pytest tests/test_search.py -v

# 4. RAG 에이전트 E2E 테스트
# - 사내 문서에 있는 내용 질문 → internal_search_tool 호출 → 내부 문서 출처 답변
# - 사내 문서에 없는 내용 질문 → internal_search_tool + web_search_tool 호출
# - supervisor가 rag_agent / chat_agent 올바르게 라우팅하는지 확인

# 5. 기존 테스트 통과 확인
python -m pytest tests/ -v
```

---

## 주요 설계 결정

| 결정 | 이유 |
|------|------|
| **Tool-based ReAct agent** | LLM이 상황에 따라 어떤 tool을 몇 번 쓸지 자율 판단. 파이프라인보다 유연 |
| **pg_bigm** | 한국어 부분 문자열 유사도 검색 지원. 한글에 맞지 않는 FTS 대신 bigram 기반 매칭 사용 |
| **별도 rag_workflow** | chat_agent(일반 대화)와 rag_agent(문서 Q&A) 역할 명확히 분리 |
| **OpenAI built-in web search** | LLM에 내장된 검색 → DuckDuckGo 대비 context 품질 우수, 별도 파싱 불필요 |
| **internal_search 우선 원칙** | 사내 보안 정보 우선 활용. 웹은 보충 역할 |
| **create_react_agent** | LangGraph prebuilt 활용 → tool loop 직접 구현 불필요 |