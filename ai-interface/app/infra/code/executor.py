# app/infra/code/executor.py
import logging
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

from app.core.config.settings import Settings
from app.infra.code.code_file_manager import CodeFileManager
from app.infra.code.constants import CodeLanguage, DEFAULT_TIMEOUT, DEFAULT_MEMORY_LIMIT, DEFAULT_CPU_LIMIT
from app.infra.docker.client import DockerClient
from app.infra.docker.constants import ExecutionStatus, DOCKER_IMAGES
from app.infra.docker.schemas import DockerExecutionResult

logger = logging.getLogger(__name__)


class DockerCodeExecutor:
    """Docker를 사용한 코드 실행기"""

    def __init__(self, docker_client: DockerClient, settings: Settings):
        self.docker_client = docker_client
        self.settings = settings

    async def execute_code(
            self,
            code: str,
            language: CodeLanguage = CodeLanguage.PYTHON,
            timeout: int = DEFAULT_TIMEOUT,
            memory_limit: str = DEFAULT_MEMORY_LIMIT,
            cpu_limit: float = DEFAULT_CPU_LIMIT,
            environment_vars: Optional[Dict[str, str]] = None
    ) -> DockerExecutionResult:
        """Docker 컨테이너에서 코드 실행 (새로운 메인 메서드)"""

        if not self.docker_client.is_available():
            return self._create_error_result("Docker 클라이언트가 사용 불가능합니다")

        # 언어 지원 확인
        if language not in DOCKER_IMAGES:
            return self._create_error_result(f"지원하지 않는 언어: {language}")

        execution_id = str(uuid.uuid4())
        start_time = time.time()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # 언어별 파일 설정 가져오기
                filename, command = CodeFileManager.get_file_config(language)

                # 코드 파일 작성
                CodeFileManager.write_code_file(temp_path, filename, code)

                return await self.docker_client.run_container(
                    execution_id=execution_id,
                    image=DOCKER_IMAGES[language],
                    command=command,
                    temp_path=temp_path,
                    environment_vars=environment_vars or {},
                    memory_limit=memory_limit,
                    cpu_limit=cpu_limit,
                    timeout=timeout,
                    start_time=start_time,
                    language=language
                )

        except Exception as e:
            logger.error(f"코드 실행 중 오류: {e}")
            return self._create_error_result(f"코드 실행 오류: {str(e)}")

    async def setup_languages(self, languages: List[CodeLanguage] = None) -> Dict[str, bool]:
        """여러 언어의 Docker 이미지들을 미리 준비"""
        if not self.docker_client.is_available():
            logger.warning("Docker 클라이언트 사용 불가능 - 이미지 준비 건너뜀")
            return {}

        if languages is None:
            languages = list(CodeLanguage)

        logger.info(f"Docker 이미지 준비 중: {[lang.value for lang in languages]}")

        results = {}
        for language in languages:
            if language in DOCKER_IMAGES:
                image = DOCKER_IMAGES[language]
                try:
                    success = await self.docker_client.pull_single_image(image)
                    results[language.value] = success

                    if success:
                        logger.info(f"이미지 준비 완료: {image}")
                    else:
                        logger.error(f"이미지 준비 실패: {image}")

                except Exception as e:
                    logger.error(f"이미지 다운로드 실패 {image}: {e}")
                    results[language.value] = False
            else:
                logger.warning(f"지원하지 않는 언어: {language}")
                results[language.value] = False

        # 결과 요약
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        logger.info(f"이미지 준비 완료: {success_count}/{total_count}")

        return results

    async def get_available_languages(self) -> List[CodeLanguage]:
        """사용 가능한 언어들 반환"""
        available = []

        if not self.docker_client.is_available():
            logger.warning("Docker 사용 불가능 - 언어 목록이 제한됩니다")
            return available

        for language in CodeLanguage:
            if language in DOCKER_IMAGES:
                # DockerClient의 자동 다운로드 기능으로 인해 모든 지원 언어를 사용 가능한 것으로 간주
                available.append(language)

        return available

    async def get_status(self) -> Dict[str, Any]:
        """실행기 상태 및 이미지 정보 반환"""
        docker_status = await self.docker_client.get_status()

        # 언어별 지원 상태 추가
        language_status = {}
        for language in CodeLanguage:
            if language in DOCKER_IMAGES:
                language_status[language.value] = {
                    "image": DOCKER_IMAGES[language],
                    "supported": True
                }
            else:
                language_status[language.value] = {
                    "supported": False
                }

        return {
            **docker_status,
            "languages": language_status
        }

    async def get_docker_status(self) -> Dict[str, Any]:
        """get_status()의 별칭 (레거시 호환성)"""
        return await self.get_status()

    def _create_error_result(self, error_message: str) -> DockerExecutionResult:
        """에러 결과 생성 헬퍼"""
        return DockerExecutionResult(
            execution_id=str(uuid.uuid4()),
            status=ExecutionStatus.FAILED,
            success=False,
            error=error_message
        )