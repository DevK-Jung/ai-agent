# app/api/v1/endpoints/search.py
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body

from app.domains.search.dependencies import SearchServiceDep
from app.domains.search.schemas import (
    SearchRequest,
    VectorSearchRequest,
    SearchResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=SearchResponse)
async def search_documents(
        search_service: SearchServiceDep,
        request: SearchRequest
):
    """문서 검색 (고급 필터링 지원)"""
    try:
        return await search_service.search_documents(request)
    except Exception as e:
        logger.error(f"문서 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=SearchResponse)
async def search_documents_simple(
        search_service: SearchServiceDep,
        q: str = Query(..., description="검색 쿼리"),
        k: int = Query(5, ge=1, le=50, description="반환할 결과 수"),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름"),
        score_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="점수 임계값")
):
    """간단한 문서 검색 (GET 방식)"""
    try:
        request = SearchRequest(
            query=q,
            k=k,
            collection_name=collection_name,
            score_threshold=score_threshold
        )
        return await search_service.search_documents(request)
    except Exception as e:
        logger.error(f"간단 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/by-vector", response_model=SearchResponse)
async def search_by_vector(
        search_service: SearchServiceDep,
        request: VectorSearchRequest
):
    """벡터로 직접 검색"""
    try:
        return await search_service.search_by_vector(request)
    except Exception as e:
        logger.error(f"벡터 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/by-metadata", response_model=SearchResponse)
async def search_by_metadata(
        search_service: SearchServiceDep,
        metadata_filter: Dict[str, Any] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름"),
        limit: int = Query(100, ge=1, le=1000, description="최대 결과 수")
):
    """메타데이터 조건으로 문서 검색"""
    try:
        return await search_service.search_by_metadata(
            metadata_filter, collection_name, limit
        )
    except Exception as e:
        logger.error(f"메타데이터 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
        search_service: SearchServiceDep,
        query: str = Body(...),
        metadata_filter: Optional[Dict[str, Any]] = Body(None),
        k: int = Body(5, ge=1, le=50),
        collection_name: Optional[str] = Body(None),
        score_threshold: Optional[float] = Body(None)
):
    """하이브리드 검색 (텍스트 + 메타데이터)"""
    try:
        return await search_service.hybrid_search(
            query=query,
            metadata_filter=metadata_filter,
            k=k,
            collection_name=collection_name,
            score_threshold=score_threshold
        )
    except Exception as e:
        logger.error(f"하이브리드 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))