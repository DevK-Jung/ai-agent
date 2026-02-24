import uuid
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks

from app.schemas.document import DocumentResponse, DocumentUploadResponse, DocumentListResponse
from app.services.document_service import DocumentService
from app.core.config import settings
from app.dependencies import get_document_service

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        domain: Optional[str] = None,
        document_service: DocumentService = Depends(get_document_service)
):
    """
    파일을 업로드하고 임베딩 처리를 백그라운드에서 수행합니다.
    
    - **file**: 업로드할 파일 (PDF, TXT, DOCX 지원)
    - **domain**: 문서가 속한 도메인 (선택적)
    - **return**: 업로드된 문서 정보와 처리 상태
    """
    # 파일 검증
    if file.content_type not in settings.ALLOWED_FILE_TYPES_LIST:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {settings.ALLOWED_FILE_TYPES_LIST}"
        )

    # 파일 크기 제한
    if file.size and file.size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"파일 크기는 {settings.MAX_FILE_SIZE_MB}MB를 초과할 수 없습니다."
        )

    try:

        # 파일 저장 및 Document 레코드 생성
        document = await document_service.create_document_from_upload(file, domain or "general")

        # 백그라운드에서 임베딩 처리
        background_tasks.add_task(
            document_service.process_document_async,
            document.id
        )

        return DocumentUploadResponse(
            id=document.id,
            title=document.title,
            file_name=document.file_name,
            file_size=document.file_size,
            file_type=document.file_type,
            status=document.status,
            message="파일이 성공적으로 업로드되었습니다. 임베딩 처리가 백그라운드에서 진행됩니다."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        document_service: DocumentService = Depends(get_document_service)
):
    """
    문서 목록을 조회합니다.
    
    - **skip**: 건너뛸 문서 수
    - **limit**: 반환할 최대 문서 수
    - **status**: 필터링할 상태 (pending, processing, completed, failed)
    """
    documents, total = await document_service.get_documents(skip, limit, status)

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                file_name=doc.file_name,
                file_size=doc.file_size,
                file_type=doc.file_type,
                status=doc.status,
                chunk_count=doc.chunk_count,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            ) for doc in documents
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
        document_id: uuid.UUID,
        document_service: DocumentService = Depends(get_document_service)
):
    """
    특정 문서의 상세 정보를 조회합니다.
    """
    document = await document_service.get_document_by_id(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    return DocumentResponse(
        id=document.id,
        title=document.title,
        file_name=document.file_name,
        file_size=document.file_size,
        file_type=document.file_type,
        status=document.status,
        chunk_count=document.chunk_count,
        created_at=document.created_at,
        updated_at=document.updated_at
    )


@router.delete("/{document_id}")
async def delete_document(
        document_id: uuid.UUID,
        document_service: DocumentService = Depends(get_document_service)
):
    """
    문서를 삭제합니다. (파일 및 모든 청크 포함)
    """
    success = await document_service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    return {"message": "문서가 성공적으로 삭제되었습니다."}
