"""
검색 API 엔드포인트
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.schemas.search import SearchRequest, SearchResponse, SearchStats
from app.services.search_service import SearchService
from app.dependencies import get_search_service

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    search_request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    의미적 검색을 수행합니다.
    
    - **query**: 검색할 질의 텍스트
    - **limit**: 반환할 최대 결과 수 (기본: 10, 최대: 50)
    - **threshold**: 유사도 임계값 (0.0-1.0, 기본: 0.5)
    - **filters**: 추가 필터링 옵션
    """
    try:
        return await search_service.semantic_search(search_request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"의미적 검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/hybrid", response_model=SearchResponse)
async def hybrid_search(
    search_request: SearchRequest,
    semantic_weight: float = Query(default=0.7, ge=0.0, le=1.0, description="의미적 검색 가중치"),
    keyword_weight: float = Query(default=0.3, ge=0.0, le=1.0, description="키워드 검색 가중치"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    하이브리드 검색 (의미적 + 키워드)을 수행합니다.
    
    - **query**: 검색할 질의 텍스트
    - **semantic_weight**: 의미적 검색 가중치 (기본: 0.7)
    - **keyword_weight**: 키워드 검색 가중치 (기본: 0.3)
    - **limit**: 반환할 최대 결과 수
    - **threshold**: 유사도 임계값
    """
    # 가중치 합이 1이 되도록 정규화
    total_weight = semantic_weight + keyword_weight
    if total_weight > 0:
        semantic_weight = semantic_weight / total_weight
        keyword_weight = keyword_weight / total_weight
    else:
        semantic_weight = 0.7
        keyword_weight = 0.3
    
    try:
        return await search_service.hybrid_search(
            search_request, keyword_weight, semantic_weight
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"하이브리드 검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/quick")
async def quick_search(
    q: str = Query(..., description="검색할 질의", min_length=1),
    limit: int = Query(default=5, ge=1, le=20, description="반환할 결과 수"),
    threshold: float = Query(default=0.5, ge=0.0, le=1.0, description="유사도 임계값"),
    search_service: SearchService = Depends(get_search_service)
):
    """
    빠른 검색을 수행합니다. (GET 방식)
    
    - **q**: 검색할 질의 텍스트
    - **limit**: 반환할 결과 수 (기본: 5, 최대: 20)  
    - **threshold**: 유사도 임계값 (기본: 0.5)
    """
    try:
        search_request = SearchRequest(
            query=q,
            limit=limit,
            threshold=threshold
        )
        return await search_service.semantic_search(search_request)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"빠른 검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/stats", response_model=SearchStats)
async def get_search_stats(
    search_service: SearchService = Depends(get_search_service)
):
    """
    검색 시스템 통계 정보를 조회합니다.
    
    - **total_documents**: 총 문서 수
    - **total_chunks**: 총 청크 수
    - **embedding_model**: 사용된 임베딩 모델
    - **embedding_dimensions**: 임베딩 차원 수
    """
    try:
        return await search_service.get_search_stats()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"검색 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )