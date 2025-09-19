# app/infra/docker/client.py
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, Optional

import docker
from docker.errors import ImageNotFound, APIError, NotFound

from app.infra.code.constants import CodeLanguage
from app.infra.docker.constants import ExecutionStatus
from app.infra.docker.schemas import DockerExecutionResult

logger = logging.getLogger(__name__)


class DockerClient:
    """Docker 실행을 담당하는 클라이언트"""

    def __init__(self):
        self.client: Optional[docker.DockerClient] = None
        self._thread_pool = ThreadPoolExecutor(max_workers=3)
        self._initialize()

    def _initialize(self) -> None:
        """Docker 클라이언트 초기화"""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker 클라이언트 초기화 완료")
        except Exception as e:
            logger.warning(f"Docker 초기화 실패: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Docker 사용 가능 여부 확인"""
        return self.client is not None

    async def _ensure_image_exists(self, image: str) -> bool:
        """이미지 존재 확인 및 필요시 다운로드"""
        try:
            self.client.images.get(image)
            logger.info(f"이미지 존재 확인: {image}")
            return True
        except ImageNotFound:
            logger.info(f"이미지 다운로드 시작: {image}")
            return await self.pull_single_image(image)

    async def run_container(
            self,
            execution_id: str,
            image: str,
            command: list,
            temp_path: Path,
            environment_vars: Dict[str, str],
            memory_limit: str,
            cpu_limit: float,
            timeout: int,
            start_time: float,
            language: CodeLanguage
    ) -> DockerExecutionResult:
        """컨테이너 실행 로직"""

        if not self.is_available():
            return self._create_error_result(
                execution_id, "Docker 클라이언트가 사용 불가능합니다", start_time
            )

        # 이미지 확인 및 다운로드
        if not await self._ensure_image_exists(image):
            return self._create_error_result(
                execution_id, f"이미지 다운로드 실패: {image}", start_time
            )

        container = None
        try:
            # 컨테이너 생성
            container = self.client.containers.create(
                image=image,
                command=command,
                volumes={str(temp_path): {'bind': '/workspace', 'mode': 'ro'}},
                environment=environment_vars,
                mem_limit=memory_limit,
                cpu_period=100000,
                cpu_quota=int(100000 * cpu_limit),
                network_disabled=True,
                detach=True
            )

            # 컨테이너 시작
            container.start()

            # 실행 완료 대기 (한 번만 호출)
            return await self._wait_for_completion(
                container, execution_id, timeout, start_time
            )

        except Exception as e:
            logger.error(f"컨테이너 실행 중 오류: {e}")
            return self._create_error_result(
                execution_id, f"컨테이너 실행 오류: {str(e)}", start_time
            )
        finally:
            await self._cleanup_container(container)

    async def _wait_for_completion(
            self,
            container,
            execution_id: str,
            timeout: int,
            start_time: float
    ) -> DockerExecutionResult:
        """컨테이너 실행 완료 대기"""
        try:
            result = container.wait(timeout=timeout)
            stdout, stderr = await self._collect_logs(container)
            execution_time = time.time() - start_time

            return DockerExecutionResult(
                execution_id=execution_id,
                status=ExecutionStatus.COMPLETED if result['StatusCode'] == 0 else ExecutionStatus.FAILED,
                success=result['StatusCode'] == 0,
                stdout=stdout,
                stderr=stderr,
                execution_time=round(execution_time, 3),
                exit_code=result['StatusCode']
            )

        except Exception as wait_error:
            logger.error(f"컨테이너 대기 중 오류: {wait_error}")

            # 실행 중인 컨테이너 강제 종료
            await self._force_stop_container(container)

            # 부분 로그 수집
            stdout, stderr = await self._collect_logs(container, safe=True)
            execution_time = time.time() - start_time

            status = ExecutionStatus.TIMEOUT if "timeout" in str(wait_error).lower() else ExecutionStatus.FAILED

            return DockerExecutionResult(
                execution_id=execution_id,
                status=status,
                success=False,
                stdout=stdout,
                stderr=stderr,
                execution_time=round(execution_time, 3),
                error=f"실행 오류: {str(wait_error)}"
            )

    async def _collect_logs(self, container, safe: bool = False) -> tuple[str, str]:
        """컨테이너 로그 수집"""
        try:
            stdout = container.logs(stdout=True, stderr=False).decode('utf-8')
            stderr = container.logs(stdout=False, stderr=True).decode('utf-8')
            return stdout, stderr
        except Exception as log_error:
            if safe:
                logger.warning(f"로그 수집 실패: {log_error}")
                return "", f"로그 수집 실패: {str(log_error)}"
            raise

    async def _force_stop_container(self, container) -> None:
        """컨테이너 강제 종료"""
        try:
            container.reload()
            if container.status == 'running':
                container.kill()
                logger.info("실행 중인 컨테이너 강제 종료")
        except Exception as e:
            logger.warning(f"컨테이너 강제 종료 실패: {e}")

    async def _cleanup_container(self, container) -> None:
        """컨테이너 정리"""
        if container:
            try:
                container.remove(force=True)
            except Exception as cleanup_error:
                logger.warning(f"컨테이너 정리 실패: {cleanup_error}")

    def _create_error_result(
            self,
            execution_id: str,
            error_message: str,
            start_time: float
    ) -> DockerExecutionResult:
        """에러 결과 생성 헬퍼"""
        execution_time = time.time() - start_time
        return DockerExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.FAILED,
            success=False,
            execution_time=round(execution_time, 3),
            error=error_message
        )

    async def get_status(self) -> Dict[str, Any]:
        """Docker 상태 확인"""
        if not self.is_available():
            return {
                "available": False,
                "error": "Docker 클라이언트 초기화 실패"
            }

        try:
            info = self.client.info()
            return {
                "available": True,
                "docker_version": info.get("ServerVersion", "unknown"),
                "containers_running": info.get("ContainersRunning", 0),
                "images_count": len(self.client.images.list())
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }

    async def pull_single_image(self, image: str) -> bool:
        """단일 이미지 다운로드"""
        try:
            logger.info(f"Docker 이미지 다운로드 시작: {image}")

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._thread_pool,
                self.client.images.pull,
                image
            )

            logger.info(f"이미지 다운로드 완료: {image}")
            return True

        except (NotFound, APIError) as e:
            logger.error(f"이미지 다운로드 실패 {image}: {e}")
            return False
        except Exception as e:
            logger.error(f"이미지 다운로드 중 예상치 못한 오류 {image}: {e}")
            return False

    async def cleanup_containers(self) -> int:
        """중단된 컨테이너들 정리"""
        if not self.is_available():
            return 0

        try:
            containers = self.client.containers.list(
                all=True,
                filters={"status": "exited"}
            )

            count = 0
            for container in containers:
                try:
                    container.remove()
                    count += 1
                except Exception:
                    continue

            logger.info(f"{count}개의 중단된 컨테이너 정리 완료")
            return count

        except Exception as e:
            logger.error(f"컨테이너 정리 실패: {e}")
            return 0

    def close(self) -> None:
        """리소스 정리"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)

        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None