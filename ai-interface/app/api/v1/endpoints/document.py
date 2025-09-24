# app/api/v1/endpoints/document.py
import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Body, Path

from app.domains.document.dependencies import DocumentServiceDep
from app.domains.document.schemas import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    FileUploadRequest,
    DocumentInfo,
    DocumentUpdateRequest,
    DocumentDeleteResponse
)
from app.domains.document.constants import ChunkingStrategy

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/text", response_model=DocumentUploadResponse)
async def upload_text_document(
        document_service: DocumentServiceDep,
        request: DocumentUploadRequest,
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """텍스트 문서 업로드"""
    try:
        return await document_service.upload_text_document(request, collection_name)
    except Exception as e:
        logger.error(f"텍스트 문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/file", response_model=DocumentUploadResponse)
async def upload_file_document(
        document_service: DocumentServiceDep,
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

        # FileUploadRequest 생성
        request = FileUploadRequest(
            file_content=file_content,
            filename=file.filename,
            metadata={},
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            chunking_strategy=chunking_strategy
        )

        return await document_service.upload_file_document(request, collection_name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 문서 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document_by_id(
        document_service: DocumentServiceDep,
        document_id: str = Path(..., description="문서 ID"),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """ID로 문서 조회"""
    try:
        document = await document_service.get_document_by_id(document_id, collection_name)
        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}")
async def update_document(
        document_service: DocumentServiceDep,
        document_id: str = Path(..., description="문서 ID"),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름"),
        request: DocumentUpdateRequest = Body(...)
):
    """문서 업데이트"""
    try:
        if not request.content and not request.metadata:
            raise HTTPException(status_code=400, detail="업데이트할 내용 또는 메타데이터를 제공해야 합니다")

        success = await document_service.update_document(document_id, request, collection_name)

        if success:
            return {"message": "문서가 성공적으로 업데이트되었습니다", "document_id": document_id}
        else:
            raise HTTPException(status_code=404, detail="업데이트할 문서를 찾을 수 없습니다")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 업데이트 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/", response_model=DocumentDeleteResponse)
async def delete_documents(
        document_service: DocumentServiceDep,
        document_ids: List[str] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """문서 삭제"""
    try:
        if not document_ids:
            raise HTTPException(status_code=400, detail="삭제할 문서 ID를 제공해야 합니다")

        return await document_service.delete_documents(document_ids, collection_name)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 삭제 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/by-metadata", response_model=Dict[str, Any])
async def bulk_delete_by_metadata(
        document_service: DocumentServiceDep,
        metadata_filter: Dict[str, Any] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름")
):
    """메타데이터 조건으로 대량 삭제"""
    try:
        deleted_count = await document_service.bulk_delete_by_metadata(
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


@router.post("/by-metadata", response_model=List[DocumentInfo])
async def get_documents_by_metadata(
        document_service: DocumentServiceDep,
        metadata_filter: Dict[str, Any] = Body(...),
        collection_name: Optional[str] = Query(None, description="컬렉션 이름"),
        limit: int = Query(100, ge=1, le=1000, description="최대 결과 수")
):
    """메타데이터 조건으로 문서 검색"""
    try:
        return await document_service.get_documents_by_metadata(
            metadata_filter, collection_name, limit
        )
    except Exception as e:
        logger.error(f"메타데이터 문서 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))