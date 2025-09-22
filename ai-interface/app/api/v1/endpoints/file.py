import logging
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Query

from app.domains.file.dependencies import FileServiceDep

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/extract", response_model=None)
async def extract_file_content(
        file_service: FileServiceDep,
        file: UploadFile = File(...),
        encoding: Optional[str] = Query(None, description="텍스트 파일 인코딩 (기본값: utf-8)"),
        sheet_name: Optional[str] = Query(None, description="Excel 특정 시트 이름")
):
    """단일 파일 내용 추출"""

    extract_options = {}
    if encoding:
        extract_options["encoding"] = encoding
    if sheet_name:
        extract_options["sheet_name"] = sheet_name

    result = await file_service.extract_file_content(file, extract_options)

    return {
        "success": True,
        "message": "파일 내용이 성공적으로 추출되었습니다.",
        "data": result
    }


@router.post("/extract/multiple", response_model=None)
async def extract_multiple_files_content(
        file_service: FileServiceDep,
        files: List[UploadFile] = File(...),
        encoding: Optional[str] = Query(None, description="텍스트 파일 인코딩")
):
    """다중 파일 내용 추출"""

    extract_options = {}
    if encoding:
        extract_options["encoding"] = encoding

    results = await file_service.extract_multiple_files(files, extract_options)

    # success_count = sum(1 for r in results if r.get("success", False))

    return {
        "success": True,
        # "message": f"{success_count}/{len(results)} 파일이 성공적으로 처리되었습니다.",
        "data": results,
        "summary": {
            "total": len(results),
            # "success": success_count,
            # "failed": len(results) - success_count
        }
    }
