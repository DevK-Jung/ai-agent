# app/api/v1/endpoints/vector.py
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body

from app.domains.vector.constants import ChunkingStrategy
# 도메인별 의존성 임포트
from app.domains.vector.dependencies import VectorServiceDep
from app.domains.vector.schemas import VectorStoreStatus, DocumentResponse, DocumentRequest, SearchResponse, \
    SearchRequest

router = APIRouter()
logger = logging.getLogger(__name__)


# ========================================
# 헬스체크 및 상태 조회
# ========================================

@router.get("/health")
async def vector_health_check(
        vector_service: VectorServiceDep
):
    """벡터 도메인 헬스체크"""
    try:
        status = await vector_service.get_status()
        return {
            "status": "healthy" if status.is_connected else "unhealthy",
            "details": status.dict()
        }
    except Exception as e:
        logger.error(f"벡터 헬스체크 실패: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/status", response_model=VectorStoreStatus)
async def get_vector_status(
        vector_service: VectorServiceDep
):
    """벡터 저장소 상태 조회"""
    try:
        return await vector_service.get_status()
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 문서 관리
# ========================================

@router.post("/documents/text", response_model=DocumentResponse)
async def upload_text_document(
        vector_service: VectorServiceDep,
        request: DocumentRequest,
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """텍스트 문서 업로드"""
    try:
        return await vector_service.add_text_document(request, collection_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"텍스트 문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/documents/file", response_model=DocumentResponse)
async def upload_file_document(
        vector_service: VectorServiceDep,
        file: UploadFile = File(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름"),
        chunk_size: Optional[int] = Query(None, ge=100, le=5000, description="청크 크기"),
        chunk_overlap: Optional[int] = Query(None, ge=0, le=1000, description="청크 겹침"),
        chunking_strategy: ChunkingStrategy = Query(ChunkingStrategy.RECURSIVE_CHARACTER, description="분할 전략")
):
    """파일 문서 업로드 (PDF, TXT, MD, HTML 지원)"""
    try:
        # 파일 크기 체크 (10MB 제한)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        file_content = await file.read()

        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="파일 크기가 10MB를 초과합니다")

        # 파일 확장자 체크
        allowed_extensions = {'.pdf', '.txt', '.md', '.html', '.htm'}
        file_ext = '.' + file.filename.lower().split('.')[-1] if '.' in file.filename else ''

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(allowed_extensions)}"
            )

        return await vector_service.add_file_document(
            file_content=file_content,
            filename=file.filename,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy,
            collection_name=collection_name
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}")
async def get_document_by_id(
        document_id: str,
        vector_service: VectorServiceDep,
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """ID로 문서 조회"""
    try:
        document = await vector_service.get_document_by_id(document_id, collection_name)
        if document:
            return {
                "document_id": document_id,
                "content": document.page_content,
                "metadata": document.metadata
            }
        else:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/documents/{document_id}")
async def update_document(
        document_id: str,
        vector_service: VectorServiceDep,
        new_content: Optional[str] = Body(None),
        new_metadata: Optional[Dict[str, Any]] = Body(None),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """문서 업데이트"""
    try:
        if not new_content and not new_metadata:
            raise HTTPException(status_code=400, detail="업데이트할 내용 또는 메타데이터를 제공해야 합니다")

        success = await vector_service.update_document(
            document_id=document_id,
            new_content=new_content,
            new_metadata=new_metadata,
            collection_name=collection_name
        )

        if success:
            return {"message": "문서가 성공적으로 업데이트되었습니다", "document_id": document_id}
        else:
            raise HTTPException(status_code=404, detail="업데이트할 문서를 찾을 수 없습니다")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents")
async def delete_documents(
        vector_service: VectorServiceDep,
        document_ids: List[str] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """문서 삭제"""
    try:
        if not document_ids:
            raise HTTPException(status_code=400, detail="삭제할 문서 ID를 제공해야 합니다")

        success = await vector_service.delete_documents(document_ids, collection_name)
        return {
            "success": success,
            "message": f"{len(document_ids)}개 문서 삭제 {'성공' if success else '실패'}",
            "deleted_ids": document_ids if success else []
        }

    except Exception as e:
        logger.error(f"문서 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/by-metadata")
async def bulk_delete_by_metadata(
        vector_service: VectorServiceDep,
        metadata_filter: Dict[str, Any] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """메타데이터 조건으로 대량 삭제"""
    try:
        deleted_count = await vector_service.bulk_delete_by_metadata(
            metadata_filter, collection_name
        )
        return {
            "success": deleted_count > 0,
            "deleted_count": deleted_count,
            "message": f"{deleted_count}개 문서 삭제 완료"
        }
    except Exception as e:
        logger.error(f"대량 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 검색 기능
# ========================================

@router.post("/search", response_model=SearchResponse)
async def search_documents(
        request: SearchRequest,
        vector_service: VectorServiceDep
):
    """문서 검색 (고급 필터링 지원)"""
    try:
        return await vector_service.search_documents(request)
    except Exception as e:
        logger.error(f"문서 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=SearchResponse)
async def search_documents_simple(
        vector_service: VectorServiceDep,
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
        return await vector_service.search_documents(request)
    except Exception as e:
        logger.error(f"간단 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/by-vector", response_model=SearchResponse)
async def search_by_vector(
        vector_service: VectorServiceDep,
        embedding: List[float] = Body(...),
        k: int = Body(5, ge=1, le=50),
        collection_name: Optional[str] = Body(None),
        metadata_filter: Optional[Dict[str, Any]] = Body(None),
        score_threshold: Optional[float] = Body(None)
):
    """벡터로 직접 검색"""
    try:
        return await vector_service.search_by_vector(
            embedding=embedding,
            k=k,
            collection_name=collection_name,
            metadata_filter=metadata_filter,
            score_threshold=score_threshold
        )
    except Exception as e:
        logger.error(f"벡터 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/by-metadata")
async def search_by_metadata(
        vector_service: VectorServiceDep,
        metadata_filter: Dict[str, Any] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름"),
        limit: int = Query(100, ge=1, le=1000, description="최대 결과 수")
):
    """메타데이터 조건으로 문서 검색"""
    try:
        documents = await vector_service.get_documents_by_metadata(
            metadata_filter=metadata_filter,
            collection_name=collection_name,
            limit=limit
        )

        return {
            "documents": [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in documents
            ],
            "count": len(documents),
            "filter": metadata_filter
        }
    except Exception as e:
        logger.error(f"메타데이터 검색 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================================
# 컬렉션 관리
# ========================================

@router.get("/collections")
async def list_collections(
        vector_service: VectorServiceDep
):
    """컬렉션 목록 조회"""
    try:
        collections = await vector_service.list_collections()
        return {"collections": collections, "count": len(collections)}
    except Exception as e:
        logger.error(f"컬렉션 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collections/{collection_name}")
async def create_collection(
        collection_name: str,
        vector_service: VectorServiceDep
):
    """컬렉션 생성"""
    try:
        success = await vector_service.create_collection(collection_name)
        return {
            "success": success,
            "message": f"컬렉션 '{collection_name}' {'생성 성공' if success else '생성 실패'}",
            "collection_name": collection_name
        }
    except Exception as e:
        logger.error(f"컬렉션 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_name}")
async def delete_collection(
        collection_name: str,
        vector_service: VectorServiceDep
):
    """컬렉션 삭제"""
    try:
        success = await vector_service.delete_collection(collection_name)
        return {
            "success": success,
            "message": f"컬렉션 '{collection_name}' {'삭제 성공' if success else '삭제 실패'}",
            "collection_name": collection_name
        }
    except Exception as e:
        logger.error(f"컬렉션 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
