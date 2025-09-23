import logging

from fastapi import APIRouter, HTTPException

from app.domains.code.dependencies import CodeServiceDep
from app.domains.code.schemas import CodeGenerationRequest, CodeGenerationResponse, CodeExecutionResponse, \
    CodeExecutionRequest

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=CodeGenerationResponse)
async def generate_code(
        request: CodeGenerationRequest,
        code_service: CodeServiceDep
):
    try:
        result = await code_service.generate_code(request)
        return result
    except Exception as e:
        logger.error(f"코드 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=CodeExecutionResponse)
async def execute_code(
        request: CodeExecutionRequest,
        code_service: CodeServiceDep
):
    try:
        result = await code_service.execute_code(request)
        return result
    except Exception as e:
        logger.error(f"코드 실행 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
