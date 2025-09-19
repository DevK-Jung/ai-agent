from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.infra.code.constants import CodeLanguage, ExecutionEnvironment
from app.infra.docker.constants import ExecutionStatus


class CodeGenerationRequest(BaseModel):
    query: str = Field(..., description="코드 생성 요청")
    context: Optional[str] = Field(None, description="추가 컨텍스트")
    modify_existing: bool = Field(False, description="기존 코드 수정 여부")
    language: CodeLanguage = Field(CodeLanguage.PYTHON, description="프로그래밍 언어")


class CodeGenerationResponse(BaseModel):
    generated_code: str = Field(..., description="생성된 코드")
    explanation: str = Field(..., description="코드 설명")
    language: str = Field(..., description="프로그래밍 언어")
    execution_ready: bool = Field(True, description="실행 가능 여부")


class CodeExecutionRequest(BaseModel):
    code: str = Field(..., description="실행할 코드")
    language: CodeLanguage = Field(CodeLanguage.PYTHON, description="프로그래밍 언어")
    environment: ExecutionEnvironment = Field(ExecutionEnvironment.DOCKER, description="실행 환경")
    timeout: int = Field(30, ge=1, le=300, description="타임아웃 (초)")
    memory_limit: str = Field("512m", description="메모리 제한")
    input_data: Optional[Dict[str, Any]] = Field(None, description="입력 데이터")
    environment_vars: Optional[Dict[str, str]] = Field(None, description="환경 변수")


class CodeExecutionResponse(BaseModel):
    execution_id: str = Field(..., description="실행 ID")
    status: ExecutionStatus = Field(..., description="실행 상태")
    success: bool = Field(..., description="실행 성공 여부")
    stdout: Optional[str] = Field(None, description="표준 출력")
    stderr: Optional[str] = Field(None, description="에러 출력")
    execution_time: float = Field(..., description="실행 시간 (초)")
    environment: ExecutionEnvironment = Field(..., description="실행 환경")
    language: str = Field(..., description="프로그래밍 언어")
    exit_code: Optional[int] = Field(None, description="종료 코드")
    variables: Optional[Dict[str, Any]] = Field(None, description="실행 결과 변수들")
    error: Optional[str] = Field(None, description="에러 메시지")
