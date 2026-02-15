"""FastAPI 예외 핸들러들"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AIAgentException,
    WorkflowException,
    LLMException,
    DocumentProcessingException,
    DatabaseException,
    ValidationException
)
from app.schemas.errors import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)


def setup_exception_handlers(app):
    """FastAPI 앱에 예외 핸들러들을 등록"""

    @app.exception_handler(WorkflowException)
    async def workflow_exception_handler(request: Request, exc: WorkflowException):
        """워크플로우 예외 핸들러"""
        logger.error(f"Workflow Exception: {exc.message}", extra={"details": exc.details})
        
        error_response = ErrorResponse(
            type="WorkflowError",
            message="워크플로우 실행 중 오류가 발생했습니다.",
            details=exc.details,
            path=str(request.url),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )

    @app.exception_handler(LLMException)
    async def llm_exception_handler(request: Request, exc: LLMException):
        """LLM 예외 핸들러"""
        logger.error(f"LLM Exception: {exc.message}", extra={"details": exc.details})
        
        error_response = ErrorResponse(
            type="LLMError",
            message="AI 모델 호출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            details=exc.details,
            path=str(request.url),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response.model_dump()
        )

    @app.exception_handler(DocumentProcessingException)
    async def document_processing_exception_handler(request: Request, exc: DocumentProcessingException):
        """문서 처리 예외 핸들러"""
        logger.error(f"Document Processing Exception: {exc.message}", extra={"details": exc.details})
        
        error_response = ErrorResponse(
            type="DocumentProcessingError",
            message="문서 처리 중 오류가 발생했습니다.",
            details=exc.details,
            path=str(request.url),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )

    @app.exception_handler(DatabaseException)
    async def database_exception_handler(request: Request, exc: DatabaseException):
        """데이터베이스 예외 핸들러"""
        logger.error(f"Database Exception: {exc.message}", extra={"details": exc.details})
        
        error_response = ErrorResponse(
            type="DatabaseError",
            message="데이터베이스 작업 중 오류가 발생했습니다.",
            details=exc.details,
            path=str(request.url),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """입력 검증 예외 핸들러"""
        logger.warning(f"Validation Exception: {exc.message}", extra={"details": exc.details})
        
        error_response = ErrorResponse(
            type="ValidationError",
            message=exc.message,
            details=exc.details,
            path=str(request.url),
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response.model_dump()
        )

    @app.exception_handler(AIAgentException)
    async def ai_agent_exception_handler(request: Request, exc: AIAgentException):
        """AI Agent 커스텀 예외 핸들러"""
        logger.error(f"AI Agent Exception: {exc.message}", extra={"details": exc.details})
        
        error_response = ErrorResponse(
            type=exc.__class__.__name__,
            message=exc.message,
            details=exc.details,
            path=str(request.url),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """HTTP 예외 핸들러"""
        logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
        
        error_response = ErrorResponse(
            type="HTTPError",
            message=exc.detail,
            path=str(request.url),
            status_code=exc.status_code
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
        """요청 검증 예외 핸들러"""
        logger.warning(f"Request Validation Exception: {exc.errors()}")
        
        # FastAPI 검증 오류를 ErrorDetail 형식으로 변환
        error_details = [
            ErrorDetail(
                field=".".join(str(loc) for loc in error["loc"][1:]) if len(error["loc"]) > 1 else str(error["loc"][0]),
                message=error["msg"],
                type=error["type"],
                input=error.get("input")
            )
            for error in exc.errors()
        ]
        
        error_response = ErrorResponse(
            type="RequestValidationError",
            message="요청 데이터가 올바르지 않습니다.",
            details=[detail.model_dump() for detail in error_details],
            path=str(request.url),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """일반 예외 핸들러 (최종 catch-all)"""
        logger.error(f"Unhandled Exception: {str(exc)}", exc_info=True)
        
        error_response = ErrorResponse(
            type="InternalServerError",
            message="서버 내부 오류가 발생했습니다. 관리자에게 문의해주세요.",
            path=str(request.url),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )