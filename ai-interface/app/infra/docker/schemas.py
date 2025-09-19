# app/infra/docker/schemas.py
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, computed_field

from app.infra.code.constants import ExecutionEnvironment
from .constants import ExecutionStatus


class DockerExecutionResult(BaseModel):
    """Docker 실행 결과를 담는 Pydantic 모델"""

    execution_id: str = Field(..., description="실행 고유 식별자")
    status: ExecutionStatus = Field(..., description="실행 상태")
    success: bool = Field(..., description="실행 성공 여부")
    stdout: str = Field(default="", description="표준 출력")
    stderr: str = Field(default="", description="표준 에러 출력")
    execution_time: float = Field(default=0.0, description="실행 시간(초)", ge=0.0)
    exit_code: Optional[int] = Field(default=None, description="프로세스 종료 코드")
    error: Optional[str] = Field(default=None, description="에러 메시지")

    @computed_field
    @property
    def environment(self) -> ExecutionEnvironment:
        """실행 환경 (항상 DOCKER)"""
        return ExecutionEnvironment.DOCKER

    class Config:
        use_enum_values = True
        extra = "forbid"

    def to_dict(self) -> Dict[str, Any]:
        """기존 호환성을 위한 메서드 (model_dump()와 동일)"""
        return self.model_dump()
