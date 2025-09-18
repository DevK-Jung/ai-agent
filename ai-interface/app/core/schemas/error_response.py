import traceback

from fastapi import Request
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    errorCode: str = Field(..., description="에러 코드", examples=["ERR_001"])
    path: str = Field(..., description="요청 경로", examples=["/api/v1/samples"])
    trace: str | None = Field(None, description="예외 트레이스 (선택)")

    @staticmethod
    def create_error_response(exc: Exception, request: Request, error_code: str = "ERR_500") -> "ErrorResponse":
        return ErrorResponse(
            errorCode=error_code,
            path=str(request.url.path),
            trace="".join(traceback.format_exception(None, exc, exc.__traceback__))
        )
