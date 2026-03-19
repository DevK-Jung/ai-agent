"""내부 하이브리드 검색 툴

vector (pgvector cosine) + keyword (pg_bigm LIKE) + RRF 융합.
@tool 없이 순수 async 함수 — node에서 직접 호출.
"""
import logging
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.dependencies import get_embedding_service
from app.models.document import Document, DocumentChunk

logger = logging.getLogger(__name__)


async def hybrid_search(
    query: str,
    keywords: list[str],
    user_id: Optional[str] = None,
) -> tuple[str, list[str]]:
    """
    hybrid search (vector + pg_bigm + RRF) 수행.

    Returns:
        (context_string, citations_list)
        - context_string: 검색 결과를 포매팅한 문자열
        - citations_list: 파일명 또는 문서 제목 목록
    """
    embedding_service = get_embedding_service()
    query_embedding = embedding_service.encode_query(query)

    async with AsyncSessionLocal() as db:
        vector_results = await _vector_search(db, query_embedding.tolist())
        bigm_results = await _bigm_search(db, keywords)
        top_chunks = _rrf_fusion(vector_results, bigm_results)

    if not top_chunks:
        return "", []

    context = _format_context(top_chunks)
    citations = list(dict.fromkeys(
        chunk.document.file_name or chunk.document.title or "Unknown"
        for chunk in top_chunks
    ))

    return context, citations


async def _vector_search(db, query_embedding: list[float]) -> list[DocumentChunk]:
    stmt = (
        select(DocumentChunk)
        .join(Document)
        .where(
            Document.status == "completed",
            DocumentChunk.embedding.isnot(None),
        )
        .options(joinedload(DocumentChunk.document))
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(settings.RAG_SEARCH_LIMIT)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _bigm_search(db, keywords: list[str]) -> list[DocumentChunk]:
    if not keywords:
        return []
    try:
        conditions = [DocumentChunk.content.ilike(f"%{kw}%") for kw in keywords]
        stmt = (
            select(DocumentChunk)
            .join(Document)
            .where(Document.status == "completed", or_(*conditions))
            .options(joinedload(DocumentChunk.document))
            .limit(settings.RAG_SEARCH_LIMIT)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    except Exception as e:
        logger.warning("pg_bigm search failed: %s", e)
        return []


def _rrf_fusion(
    vector_results: list[DocumentChunk],
    bigm_results: list[DocumentChunk],
) -> list[DocumentChunk]:
    """Reciprocal Rank Fusion: score = sum(1 / (k + rank))"""
    k = settings.RAG_RRF_K
    scores: dict[str, float] = {}
    chunk_map: dict[str, DocumentChunk] = {}

    for rank, chunk in enumerate(vector_results, start=1):
        cid = str(chunk.id)
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        chunk_map[cid] = chunk

    for rank, chunk in enumerate(bigm_results, start=1):
        cid = str(chunk.id)
        scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
        chunk_map[cid] = chunk

    sorted_ids = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [chunk_map[cid] for cid in sorted_ids[: settings.RAG_TOP_K]]


def _format_context(chunks: list[DocumentChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        title = chunk.document.file_name or chunk.document.title or "Unknown"
        parts.append(f"[{i}] 출처: {title}\n{chunk.content}")
    return "\n\n".join(parts)
