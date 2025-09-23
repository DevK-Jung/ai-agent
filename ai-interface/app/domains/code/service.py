import logging
import re
import time

from app.core.config.settings import Settings
from .schemas import (
    CodeGenerationRequest, CodeGenerationResponse,
    CodeExecutionRequest, CodeExecutionResponse
)
from ..file.schemas import FileExtractionResult
from ...infra.ai.llm.constants import LLMProvider
from ...infra.ai.llm.llm_manager import LLMManager
from ...infra.ai.llm.schemas import ChatMessage, LLMRequest
from ...infra.ai.prompt.constants import PromptRole, PromptType
from ...infra.code.executor import DockerCodeExecutor
from ...infra.docker.constants import ExecutionStatus

logger = logging.getLogger(__name__)


class CodeService:

    def __init__(self,
                 code_executor: DockerCodeExecutor,
                 llm_manager: LLMManager,
                 settings: Settings):

        self.code_executor = code_executor
        self.llm_manager = llm_manager
        self.settings = settings

    async def generate_code(self,
                            request: CodeGenerationRequest,
                            file_content: FileExtractionResult | None) -> CodeGenerationResponse:
        """코드 생성"""
        try:

            # LLMRequest 생성
            llm_request = self._create_llm_request(request, file_content)

            # chat blocking 호출
            response = await self.llm_manager.generate_response(llm_request)

            # 응답에서 코드와 설명 추출
            code, explanation = self._extract_code_and_explanation(response.content, request.language.value)

            return CodeGenerationResponse(
                generated_code=code,
                explanation=explanation,
                language=request.language.value,
                execution_ready=True
            )

        except Exception as e:
            logger.error(f"코드 생성 실패: {e}")
            raise

    def _create_llm_request(self, request: CodeGenerationRequest, file_content: FileExtractionResult | None) -> LLMRequest:

        messages = [ChatMessage(role=PromptRole.USER.value, content=request.query)]

        # LLMRequest 생성
        llm_request = LLMRequest(
            messages=messages,
            domain=PromptType.CODE_GENERATION.value,
            parameters={"language": request.language.value},
            provider=LLMProvider.OLLAMA,
            llm_config=None,
            file_info=file_content,
        )

        return llm_request

    def _extract_code_and_explanation(self, content: str, language: str) -> tuple[str, str]:
        """응답에서 코드와 설명을 추출"""
        # 코드 블록 추출
        code_pattern = rf'```(?:{language})?\n(.*?)```'
        code_matches = re.findall(code_pattern, content, re.DOTALL)

        if code_matches:
            code = code_matches[0].strip()
        else:
            # 코드 블록이 없으면 전체 응답을 코드로 처리
            code = content.strip()

        # 설명 추출 (전체 설명 포함)
        explanation_patterns = [
            r'\*\*설명:\*\*(.*)',  # **설명:** 이후 모든 내용
            r'\*\*변경사항 설명:\*\*(.*)',  # **변경사항 설명:** 이후 모든 내용
            r'설명:(.*?)(?:\n\n|$)',  # 기존 패턴 유지
        ]

        explanation = ""
        for pattern in explanation_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                explanation = match.group(1).strip()
                break

        if not explanation:
            # 패턴으로 찾지 못하면 코드 이후 텍스트를 설명으로 사용
            parts = content.split('```')
            if len(parts) > 2:
                explanation = parts[-1].strip()
            else:
                explanation = f"{language.title()} 코드가 생성되었습니다."

        return code, explanation

    async def execute_code(self, request: CodeExecutionRequest) -> CodeExecutionResponse:
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
