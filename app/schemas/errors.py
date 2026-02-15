"""에러 응답 스키마"""
from typing import Any, Dict, Optional, List, Union
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    field: Optional[str] = None
    message: str
    type: Optional[str] = None
    input: Optional[Any] = None


class ErrorResponse(BaseModel):
    """표준 에러 응답"""
    error: bool = True
    type: str
    message: str
    path: Optional[str] = None
    details: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None
    status_code: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": True,
                "type": "ValidationError",
                "message": "입력 데이터가 올바르지 않습니다.",
                "path": "/chat/",
                "details": {
                    "field": "message",
                    "original_error": "메시지가 비어있습니다."
                },
                "status_code": 400
            }
        }
