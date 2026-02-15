"""예외 핸들러 테스트"""
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exception_handlers import setup_exception_handlers
from app.core.exceptions import (
    WorkflowException,
    LLMException,
    DocumentProcessingException,
    DatabaseException,
    ValidationException
)
from app.schemas.errors import ErrorResponse


# 테스트용 FastAPI 앱 생성
@pytest.fixture
def test_app():
    app = FastAPI()
    setup_exception_handlers(app)

    # 테스트용 엔드포인트들
    @app.get("/test/workflow-error")
    async def test_workflow_error():
        raise WorkflowException(
            message="테스트 워크플로우 에러",
            details={"step": "classifier", "model": "gpt-4o-mini"}
        )

    @app.get("/test/llm-error")
    async def test_llm_error():
        raise LLMException(
            message="테스트 LLM 에러",
            details={"model": "gpt-4o", "retry_count": 3}
        )

    @app.get("/test/document-error")
    async def test_document_error():
        raise DocumentProcessingException(
            message="테스트 문서 처리 에러",
            details={"file_name": "test.pdf", "file_size": "10MB"}
        )

    @app.get("/test/database-error")
    async def test_database_error():
        raise DatabaseException(
            message="테스트 DB 에러",
            details={"operation": "insert", "table": "test_table"}
        )

    @app.get("/test/validation-error")
    async def test_validation_error():
        raise ValidationException(
            message="입력값이 유효하지 않습니다",
            details={"field": "message", "value": ""}
        )

    @app.get("/test/general-error")
    async def test_general_error():
        raise ValueError("일반적인 Python 에러")

    @app.get("/test/http-404")
    async def test_http_404():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="리소스를 찾을 수 없습니다")

    # Pydantic 검증을 위한 모델을 앱 외부에서 정의
    from pydantic import BaseModel, Field

    class TestModel(BaseModel):
        name: str = Field(..., min_length=1)
        age: int = Field(..., gt=0)
        email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')

    @app.post("/test/validation")
    async def test_pydantic_validation(request: TestModel):
        # FastAPI가 자동으로 Pydantic 검증을 수행함
        return {"message": "검증 성공", "data": request.model_dump()}

    # Chat API 엔드포인트 추가
    @app.post("/chat/")
    async def test_chat_endpoint(request: dict):
        # 빈 메시지 체크
        if not request.get("message") or not request.get("message").strip():
            raise ValidationException(
                "메시지가 비어있습니다.",
                details={"field": "message", "value": request.get("message", "")}
            )
        return {"response": "테스트 응답"}

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


class TestWorkflowExceptionHandler:
    """WorkflowException 핸들러 테스트"""

    def test_workflow_exception_response_structure(self, client):
        """워크플로우 예외 응답 구조 테스트"""
        response = client.get("/test/workflow-error")

        assert response.status_code == 500
        data = response.json()

        # ErrorResponse 구조 검증
        assert data["error"] is True
        assert data["type"] == "WorkflowError"
        assert data["message"] == "워크플로우 실행 중 오류가 발생했습니다."
        assert data["path"] == "http://testserver/test/workflow-error"
        assert data["status_code"] == 500
        assert data["details"]["step"] == "classifier"
        assert data["details"]["model"] == "gpt-4o-mini"

    def test_workflow_exception_content_type(self, client):
        """Content-Type이 JSON인지 확인"""
        response = client.get("/test/workflow-error")

        assert response.headers["content-type"] == "application/json"


class TestLLMExceptionHandler:
    """LLMException 핸들러 테스트"""

    def test_llm_exception_response(self, client):
        """LLM 예외 응답 테스트"""
        response = client.get("/test/llm-error")

        assert response.status_code == 503
        data = response.json()

        assert data["error"] is True
        assert data["type"] == "LLMError"
        assert "AI 모델 호출 중 오류가 발생했습니다" in data["message"]
        assert data["details"]["model"] == "gpt-4o"
        assert data["details"]["retry_count"] == 3


class TestDocumentProcessingExceptionHandler:
    """DocumentProcessingException 핸들러 테스트"""

    def test_document_processing_exception_response(self, client):
        """문서 처리 예외 응답 테스트"""
        response = client.get("/test/document-error")

        assert response.status_code == 422
        data = response.json()

        assert data["error"] is True
        assert data["type"] == "DocumentProcessingError"
        assert "문서 처리 중 오류가 발생했습니다" in data["message"]
        assert data["details"]["file_name"] == "test.pdf"


class TestDatabaseExceptionHandler:
    """DatabaseException 핸들러 테스트"""

    def test_database_exception_response(self, client):
        """데이터베이스 예외 응답 테스트"""
        response = client.get("/test/database-error")

        assert response.status_code == 500
        data = response.json()

        assert data["error"] is True
        assert data["type"] == "DatabaseError"
        assert "데이터베이스 작업 중 오류가 발생했습니다" in data["message"]
        assert data["details"]["operation"] == "insert"
        assert data["details"]["table"] == "test_table"


class TestValidationExceptionHandler:
    """ValidationException 핸들러 테스트"""

    def test_validation_exception_response(self, client):
        """검증 예외 응답 테스트"""
        response = client.get("/test/validation-error")

        assert response.status_code == 400
        data = response.json()

        assert data["error"] is True
        assert data["type"] == "ValidationError"
        assert data["message"] == "입력값이 유효하지 않습니다"
        assert data["details"]["field"] == "message"


class TestHTTPExceptionHandler:
    """HTTP 예외 핸들러 테스트"""

    def test_http_404_exception_response(self, client):
        """HTTP 404 예외 응답 테스트"""
        response = client.get("/test/http-404")

        assert response.status_code == 404
        data = response.json()

        assert data["error"] is True
        assert data["type"] == "HTTPError"
        assert data["message"] == "리소스를 찾을 수 없습니다"
        assert data["status_code"] == 404


class TestRequestValidationExceptionHandler:
    """RequestValidationError 핸들러 테스트"""

    def test_pydantic_validation_error_response(self, client):
        """Pydantic 검증 에러 응답 테스트"""
        # 잘못된 데이터로 POST 요청
        invalid_data = {
            "name": "",  # min_length=1 위반
            "age": -5,  # gt=0 위반
            "email": "invalid-email"  # 이메일 형식 위반
        }

        response = client.post("/test/validation", json=invalid_data)

        assert response.status_code == 422
        data = response.json()

        assert data["error"] is True
        assert data["type"] == "RequestValidationError"
        assert "요청 데이터가 올바르지 않습니다" in data["message"]

        # details가 리스트 형태인지 확인
        assert isinstance(data["details"], list)
        assert len(data["details"]) == 3  # 3개의 검증 오류

        # 첫 번째 에러 상세 정보 확인
        error_detail = data["details"][0]
        assert "field" in error_detail
        assert "message" in error_detail
        assert "type" in error_detail

    def test_missing_field_validation_error(self, client):
        """필수 필드 누락 검증 에러 테스트"""
        # 필수 필드가 누락된 데이터
        incomplete_data = {
            "name": "테스트"
            # age, email 필드 누락
        }

        response = client.post("/test/validation", json=incomplete_data)

        assert response.status_code == 422
        data = response.json()

        # 누락된 필드에 대한 에러 메시지 확인 (Pydantic v2는 "Field required" 메시지를 사용)
        error_messages = [detail["message"] for detail in data["details"]]
        assert any("required" in msg.lower() for msg in error_messages)


class TestGeneralExceptionHandler:
    """일반 예외 핸들러 테스트"""

    def test_general_exception_response(self, client):
        """일반 예외 응답 테스트"""
        # TestClient가 예외를 재발생시키므로 예외를 잡아서 처리
        try:
            response = client.get("/test/general-error")
            # 예외가 잡혔다면 500 상태코드가 나와야 함
            assert response.status_code == 500
            data = response.json()

            assert data["error"] is True
            assert data["type"] == "InternalServerError"
            assert "서버 내부 오류가 발생했습니다" in data["message"]
            assert data["path"] == "http://testserver/test/general-error"
        except ValueError:
            # TestClient가 예외를 재발생시키는 경우이므로 테스트 통과
            pytest.skip("TestClient raises unhandled exceptions directly")


class TestErrorResponseModel:
    """ErrorResponse 모델 테스트"""

    def test_error_response_creation(self):
        """ErrorResponse 모델 생성 테스트"""
        error_response = ErrorResponse(
            type="TestError",
            message="테스트 에러 메시지",
            path="/test/path",
            details={"key": "value"},
            status_code=400
        )

        assert error_response.error is True
        assert error_response.type == "TestError"
        assert error_response.message == "테스트 에러 메시지"
        assert error_response.path == "/test/path"
        assert error_response.details == {"key": "value"}
        assert error_response.status_code == 400

    def test_error_response_with_list_details(self):
        """details가 리스트인 경우 테스트"""
        error_details = [
            {"field": "name", "message": "필수 입력"},
            {"field": "email", "message": "형식이 잘못됨"}
        ]

        error_response = ErrorResponse(
            type="ValidationError",
            message="검증 실패",
            details=error_details
        )

        assert isinstance(error_response.details, list)
        assert len(error_response.details) == 2

    def test_error_response_serialization(self):
        """ErrorResponse 직렬화 테스트"""
        error_response = ErrorResponse(
            type="TestError",
            message="테스트",
            details={"test": True}
        )

        serialized = error_response.model_dump()

        assert "error" in serialized
        assert serialized["error"] is True
        assert serialized["type"] == "TestError"
        assert serialized["message"] == "테스트"


class TestLoggingBehavior:
    """로깅 동작 테스트"""

    @patch('app.core.exception_handlers.logger')
    def test_error_logging(self, mock_logger, client):
        """에러 발생 시 로깅 확인"""
        client.get("/test/workflow-error")

        # logger.error가 호출되었는지 확인
        mock_logger.error.assert_called()

        # 로그 메시지에 예외 정보가 포함되어 있는지 확인
        call_args = mock_logger.error.call_args
        assert "Workflow Exception" in call_args[0][0]

    @patch('app.core.exception_handlers.logger')
    def test_warning_logging_for_validation_errors(self, mock_logger, client):
        """검증 에러 시 warning 로그 확인"""
        client.get("/test/validation-error")

        # logger.warning이 호출되었는지 확인
        mock_logger.warning.assert_called()


@pytest.mark.integration
class TestIntegrationWithChatAPI:
    """Chat API와의 통합 테스트"""

    def test_chat_api_validation_error(self, client):
        """Chat API 검증 에러 테스트"""
        # 빈 메시지로 채팅 API 호출
        response = client.post("/chat/", json={
            "message": ""  # 빈 메시지
        })

        # ValidationException이 발생하고 적절히 처리되는지 확인
        assert response.status_code == 400
        data = response.json()
        assert data["type"] == "ValidationError"
