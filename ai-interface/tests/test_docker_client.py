# tests/test_docker_client.py
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import docker
import pytest

from app.infra.code.constants import CodeLanguage
from app.infra.docker.client import DockerClient
from app.infra.docker.constants import ExecutionStatus


class TestDockerClientUnit:
    """단위 테스트 - Mock 사용"""

    @pytest.fixture
    def mock_docker_client(self):
        """Mock된 Docker 클라이언트"""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True

            client = DockerClient()
            yield client, mock_client

    def test_initialization_success(self):
        """Docker 클라이언트 정상 초기화"""
        with patch("docker.from_env") as mock_docker:
            mock_client = Mock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True

            client = DockerClient()

            assert client.is_available() is True
            mock_docker.assert_called_once()
            mock_client.ping.assert_called_once()

    def test_initialization_failure(self):
        """Docker 초기화 실패 시 처리"""
        with patch("docker.from_env") as mock_docker:
            mock_docker.side_effect = Exception("Docker daemon not running")

            client = DockerClient()

            assert client.is_available() is False
            assert client.client is None

    @pytest.mark.asyncio
    async def test_run_container_success(self, mock_docker_client):
        """컨테이너 정상 실행 테스트"""
        client, mock_client = mock_docker_client

        # Mock 컨테이너 설정
        mock_container = Mock()
        mock_client.containers.create.return_value = mock_container
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.side_effect = [
            b"Hello World",  # stdout
            b""  # stderr
        ]

        # 테스트 실행
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await client.run_container(
                execution_id="test-123",
                image="python:3.9-slim",
                command=["python", "-c", "print('Hello World')"],
                temp_path=Path(temp_dir),
                environment_vars={},
                memory_limit="128m",
                cpu_limit=0.5,
                timeout=30,
                start_time=time.time(),
                language=CodeLanguage.PYTHON
            )

        # 검증
        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED.value
        assert result.stdout == "Hello World"
        assert result.stderr == ""
        assert result.exit_code == 0

        # Mock 호출 검증
        mock_client.containers.create.assert_called_once()
        mock_container.start.assert_called_once()
        mock_container.wait.assert_called_once()
        mock_container.remove.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_container_failure(self, mock_docker_client):
        """컨테이너 실행 실패 테스트"""
        client, mock_client = mock_docker_client

        # Mock 컨테이너 설정 (실패 케이스)
        mock_container = Mock()
        mock_client.containers.create.return_value = mock_container
        mock_container.wait.return_value = {'StatusCode': 1}
        mock_container.logs.side_effect = [
            b"",  # stdout
            b"SyntaxError: invalid syntax"  # stderr
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await client.run_container(
                execution_id="test-456",
                image="python:3.9-slim",
                command=["python", "-c", "invalid syntax"],
                temp_path=Path(temp_dir),
                environment_vars={},
                memory_limit="128m",
                cpu_limit=0.5,
                timeout=30,
                start_time=time.time(),
                language=CodeLanguage.PYTHON
            )

        # 검증
        assert result.success is False
        assert result.status == ExecutionStatus.FAILED.value
        assert result.exit_code == 1
        assert "SyntaxError" in result.stderr

    @pytest.mark.asyncio
    async def test_run_container_timeout(self, mock_docker_client):
        """컨테이너 타임아웃 테스트"""
        client, mock_client = mock_docker_client

        # Mock 컨테이너 설정 (타임아웃)
        mock_container = Mock()
        mock_client.containers.create.return_value = mock_container
        mock_container.wait.side_effect = Exception("timeout")
        mock_container.status = 'running'
        mock_container.logs.side_effect = [b"partial output", b""]

        with tempfile.TemporaryDirectory() as temp_dir:
            result = await client.run_container(
                execution_id="test-timeout",
                image="python:3.9-slim",
                command=["python", "-c", "import time; time.sleep(100)"],
                temp_path=Path(temp_dir),
                environment_vars={},
                memory_limit="128m",
                cpu_limit=0.5,
                timeout=1,
                start_time=time.time(),
                language=CodeLanguage.PYTHON
            )

        # 검증
        assert result.success is False
        assert result.status == ExecutionStatus.TIMEOUT.value
        mock_container.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_container_image_not_found(self, mock_docker_client):
        """이미지 없을 때 자동 다운로드 테스트"""
        client, mock_client = mock_docker_client

        # 첫 번째 호출은 ImageNotFound, 두 번째는 성공
        mock_container = Mock()
        mock_client.containers.create.side_effect = [
            docker.errors.ImageNotFound("Image not found"),
            mock_container
        ]
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.side_effect = [b"success", b""]

        # pull_single_image 메서드 모킹
        with patch.object(client, 'pull_single_image', new_callable=AsyncMock) as mock_pull:
            mock_pull.return_value = True

            with tempfile.TemporaryDirectory() as temp_dir:
                result = await client.run_container(
                    execution_id="test-pull",
                    image="custom:latest",
                    command=["echo", "test"],
                    temp_path=Path(temp_dir),
                    environment_vars={},
                    memory_limit="128m",
                    cpu_limit=0.5,
                    timeout=30,
                    start_time=time.time(),
                    language=CodeLanguage.PYTHON
                )

        # 검증
        assert result.success is True
        mock_pull.assert_called_once_with("custom:latest")

    @pytest.mark.asyncio
    async def test_get_status_success(self, mock_docker_client):
        """Docker 상태 확인 성공"""
        client, mock_client = mock_docker_client

        mock_client.info.return_value = {
            "ServerVersion": "20.10.17",
            "ContainersRunning": 3
        }
        mock_client.images.list.return_value = [Mock(), Mock()]  # 2개 이미지

        status = await client.get_status()

        assert status["available"] is True
        assert status["docker_version"] == "20.10.17"
        assert status["containers_running"] == 3
        assert status["images_count"] == 2

    @pytest.mark.asyncio
    async def test_get_status_unavailable(self):
        """Docker 사용 불가능한 경우"""
        with patch("docker.from_env") as mock_docker:
            mock_docker.side_effect = Exception("Docker not available")

            client = DockerClient()
            status = await client.get_status()

            assert status["available"] is False
            assert "error" in status

    @pytest.mark.asyncio
    async def test_pull_single_image_success(self, mock_docker_client):
        """이미지 다운로드 성공"""
        client, mock_client = mock_docker_client

        # run_in_executor 모킹
        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(return_value=Mock())

            result = await client.pull_single_image("python:3.9-slim")

            assert result is True
            mock_loop.return_value.run_in_executor.assert_called_once()

    @pytest.mark.asyncio
    async def test_pull_single_image_not_found(self, mock_docker_client):
        """존재하지 않는 이미지 다운로드"""
        client, mock_client = mock_docker_client

        with patch('asyncio.get_event_loop') as mock_loop:
            mock_loop.return_value.run_in_executor = AsyncMock(
                side_effect=docker.errors.NotFound("Image not found")
            )

            result = await client.pull_single_image("nonexistent:latest")

            assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_containers(self, mock_docker_client):
        """중단된 컨테이너 정리"""
        client, mock_client = mock_docker_client

        # Mock 중단된 컨테이너들
        mock_container1 = Mock()
        mock_container2 = Mock()
        mock_client.containers.list.return_value = [mock_container1, mock_container2]

        count = await client.cleanup_containers()

        assert count == 2
        mock_container1.remove.assert_called_once()
        mock_container2.remove.assert_called_once()
        mock_client.containers.list.assert_called_once_with(
            all=True,
            filters={"status": "exited"}
        )

    def test_close(self, mock_docker_client):
        """Docker 클라이언트 종료"""
        client, mock_client = mock_docker_client

        client.close()

        mock_client.close.assert_called_once()
        assert client.client is None


@pytest.mark.integration
class TestDockerClientIntegration:
    """통합 테스트 - 실제 Docker 사용"""

    @pytest.fixture(scope="class")
    def docker_available(self):
        """Docker 사용 가능 여부 확인"""
        try:
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            pytest.skip("Docker is not available")

    @pytest.fixture
    def docker_client(self, docker_available):
        """실제 DockerClient 인스턴스"""
        client = DockerClient()
        yield client
        client.close()

    @pytest.mark.asyncio
    async def test_real_python_execution(self, docker_client):

        image = "python:3.9-slim"

        try:
            docker_client.client.images.remove(image, force=True)
        except:
            pass

        result = await docker_client.pull_single_image(image)

        print(f"이미지 다운로드 결과: {result}")
        assert result is True

        """실제 Python 코드 실행"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 테스트 파일 생성
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("print('Hello from Docker!')\nprint(2 + 2)")

            result = await docker_client.run_container(
                execution_id="integration-test-1",
                image=image,
                command=["python", "/workspace/test.py"],
                temp_path=Path(temp_dir),
                environment_vars={},
                memory_limit="128m",
                cpu_limit=0.5,
                timeout=30,
                start_time=time.time(),
                language=CodeLanguage.PYTHON
            )

        print(f"실행 결과: {result}")

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED.value
        assert "Hello from Docker!" in result.stdout
        assert "4" in result.stdout
        assert result.exit_code == 0
        assert result.execution_time > 0

    @pytest.mark.asyncio
    async def test_real_error_handling(self, docker_client):
        """실제 오류 상황 처리"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 문법 오류가 있는 파일
            test_file = Path(temp_dir) / "error.py"
            test_file.write_text("print('Hello'\nprint 'invalid syntax'")  # 의도적 문법 오류

            result = await docker_client.run_container(
                execution_id="integration-error",
                image="python:3.9-slim",
                command=["python", "/workspace/error.py"],
                temp_path=Path(temp_dir),
                environment_vars={},
                memory_limit="128m",
                cpu_limit=0.5,
                timeout=30,
                start_time=time.time(),
                language=CodeLanguage.PYTHON
            )

        print(f"오류 결과: {result}")

        assert result.success is False
        assert result.status == ExecutionStatus.FAILED
        assert result.exit_code != 0
        assert "SyntaxError" in result.stderr or "invalid syntax" in result.stderr

    @pytest.mark.asyncio
    async def test_real_timeout(self, docker_client):
        """실제 타임아웃 처리"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 긴 시간 실행되는 코드
            test_file = Path(temp_dir) / "timeout.py"
            test_file.write_text("import time\ntime.sleep(10)\nprint('Should not reach here')")

            start_time = time.time()
            result = await docker_client.run_container(
                execution_id="integration-timeout",
                image="python:3.9-slim",
                command=["python", "/workspace/timeout.py"],
                temp_path=Path(temp_dir),
                environment_vars={},
                memory_limit="128m",
                cpu_limit=0.5,
                timeout=2,  # 2초 타임아웃
                start_time=start_time,
                language=CodeLanguage.PYTHON
            )

        print(f"타임아웃 결과: {result}")

        assert result.success is False
        assert result.status == ExecutionStatus.TIMEOUT
        assert result.execution_time <= 5  # 타임아웃으로 인해 짧아야 함
        assert "Should not reach here" not in result.stdout

    @pytest.mark.asyncio
    async def test_real_image_pull(self, docker_client):
        """실제 이미지 다운로드 테스트"""
        # 작은 이미지 사용
        image = "hello-world:latest"

        # 기존 이미지 삭제 (있다면)
        try:
            docker_client.client.images.remove(image, force=True)
        except:
            pass

        result = await docker_client.pull_single_image(image)

        print(f"이미지 다운로드 결과: {result}")
        assert result is True

        # 이미지가 실제로 존재하는지 확인
        images = docker_client.client.images.list()
        image_names = [tag for img in images for tag in img.tags]
        assert any(image in name for name in image_names)

    @pytest.mark.asyncio
    async def test_real_status_check(self, docker_client):
        """실제 Docker 상태 확인"""
        status = await docker_client.get_status()

        print(f"Docker 상태: {status}")

        assert status["available"] is True
        assert "docker_version" in status
        assert "containers_running" in status
        assert "images_count" in status
        assert isinstance(status["images_count"], int)

    @pytest.mark.asyncio
    async def test_real_cleanup_containers(self, docker_client):
        """실제 컨테이너 정리"""
        # 테스트용 컨테이너 생성 (즉시 종료되도록)
        real_client = docker_client.client

        # 몇 개의 테스트 컨테이너 생성
        containers = []
        for i in range(2):
            container = real_client.containers.run(
                "alpine:latest",
                command="echo 'test'",
                detach=True,
                name=f"test-cleanup-{i}-{int(time.time())}"
            )
            containers.append(container)

        # 컨테이너들이 종료될 때까지 대기
        for container in containers:
            container.wait()

        # 정리 실행
        count = await docker_client.cleanup_containers()

        print(f"정리된 컨테이너 수: {count}")
        assert count >= len(containers)  # 최소한 우리가 만든 컨테이너들은 정리되어야 함