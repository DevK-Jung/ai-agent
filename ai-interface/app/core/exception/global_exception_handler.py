from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.core.schemas.error_response import ErrorResponse


def register_global_exception_handlers(app: FastAPI):
    """
    FastAPI 애플리케이션에 전역 예외 핸들러를 등록합니다.
    - HTTP 예외
    - 요청 유효성 검사 예외
    - 일반 예외 (500 Internal Error)
    """

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """
        HTTPException (예: 404 Not Found, 403 Forbidden 등)을 처리하는 핸들러
        """

        err = ErrorResponse(
            errorCode=f"HTTP_{exc.status_code}",
            path=str(request.url.path),
            trace=str(exc.detail)
        )
        return JSONResponse(status_code=exc.status_code,
                            content=err.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """
        요청 데이터 유효성 검사 실패(RequestValidationError)를 처리하는 핸들러
        """

        err = ErrorResponse(
            errorCode="VALIDATION_ERROR",
            path=str(request.url.path),
            trace=str(exc.errors())
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content=err.model_dump())

    # Generic 예외 처리
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        """
        모든 예외(Exception)를 처리하는 기본 핸들러
        """

        err = ErrorResponse.create_error_response(exc, request)

        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content=err.model_dump())
