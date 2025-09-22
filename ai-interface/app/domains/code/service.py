import logging
import time

from app.core.config.settings import Settings
from .code_generator import CodeGenerator
from .schemas import (
    CodeGenerationRequest, CodeGenerationResponse,
    CodeExecutionRequest, CodeExecutionResponse
)
from ...infra.code.executor import DockerCodeExecutor
from ...infra.docker.constants import ExecutionStatus

logger = logging.getLogger(__name__)


class CodeService:

    def __init__(self, code_executor: DockerCodeExecutor, settings: Settings):
        self.code_executor = code_executor
        self.settings = settings
        self.generator = CodeGenerator()

    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResponse:
        """코드 생성"""
        try:
            # 기존 코드 생성기 사용
            result = await self.generator.generate_code(
                query=request.query,
                context=request.context,
                modify_existing=request.modify_existing
            )

            return CodeGenerationResponse(
                generated_code=result["code"],
                explanation=result["explanation"],
                language=request.language.value,
                execution_ready=True
            )

        except Exception as e:
            logger.error(f"코드 생성 실패: {e}")
            raise

    async def execute_code(
            self,
            request: CodeExecutionRequest
    ) -> CodeExecutionResponse:
        """코드 실행"""
        start_time = time.time()

        try:
            result = await self.code_executor.execute_code(
                code=request.code,
                language=request.language,
                timeout=request.timeout,
                memory_limit=request.memory_limit,
                environment_vars=request.environment_vars
            )

            return CodeExecutionResponse(**result.model_dump())

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"코드 실행 실패: {e}")

            # 에러 응답 생성
            return CodeExecutionResponse(
                execution_id="error",
                status=ExecutionStatus.FAILED,
                success=False,
                stdout=None,
                stderr=None,
                execution_time=round(execution_time, 3),
                environment=request.environment,
                language=request.language.value,
                exit_code=None,
                variables=None,
                error=str(e)
            )
