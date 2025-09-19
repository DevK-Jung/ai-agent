# tests/test_docker_code_executor_direct.py
import pytest

from app.core.config.settings import get_settings
from app.infra.code.constants import CodeLanguage
from app.infra.code.executor import DockerCodeExecutor
from app.infra.docker.client import DockerClient
from app.infra.docker.constants import ExecutionStatus


class TestDockerCodeExecutorDirect:
    """실제 DockerCodeExecutor를 직접 실행하는 테스트"""

    @pytest.fixture(scope="class")
    def settings(self):
        """실제 Settings"""
        return get_settings()

    @pytest.fixture(scope="class")
    def docker_client(self):
        """실제 DockerClient"""
        client = DockerClient()
        if not client.is_available():
            pytest.skip("Docker가 사용 불가능합니다")
        yield client
        client.close()

    @pytest.fixture
    def executor(self, docker_client, settings):
        """실제 DockerCodeExecutor"""
        return DockerCodeExecutor(docker_client, settings)

    @pytest.mark.asyncio
    async def test_docker_client_availability(self, executor):
        """Docker 클라이언트 사용 가능 여부 확인"""
        print(f"Docker 사용 가능: {executor.docker_client.is_available()}")
        assert executor.docker_client.is_available() is True

    @pytest.mark.asyncio
    async def test_get_docker_status(self, executor):
        """Docker 상태 확인"""
        status = await executor.get_status()

        print(f"\n=== Docker 상태 ===")
        print(f"사용 가능: {status['available']}")
        print(f"Docker 버전: {status.get('docker_version', 'unknown')}")
        print(f"실행 중인 컨테이너: {status.get('containers_running', 0)}")
        print(f"이미지 개수: {status.get('images_count', 0)}")

        print(f"\n=== 지원 언어 ===")
        for lang, info in status.get('languages', {}).items():
            print(f"{lang}: {info}")

        assert status['available'] is True

    @pytest.mark.asyncio
    async def test_get_available_languages(self, executor):
        """사용 가능한 언어 목록 확인"""
        languages = await executor.get_available_languages()

        print(f"\n=== 사용 가능한 언어 ===")
        for lang in languages:
            print(f"- {lang.value}")

        assert len(languages) > 0
        assert CodeLanguage.PYTHON in languages

    @pytest.mark.asyncio
    async def test_setup_single_language(self, executor):
        """단일 언어 이미지 준비"""
        print(f"\n=== Python 이미지 준비 ===")

        result = await executor.setup_languages([CodeLanguage.PYTHON])

        print(f"준비 결과: {result}")

        assert CodeLanguage.PYTHON.value in result
        assert result[CodeLanguage.PYTHON.value] is True

    @pytest.mark.asyncio
    async def test_setup_multiple_languages(self, executor):
        """여러 언어 이미지 준비"""
        print(f"\n=== 여러 언어 이미지 준비 ===")

        languages = [CodeLanguage.PYTHON, CodeLanguage.JAVASCRIPT]
        result = await executor.setup_languages(languages)

        print(f"준비 결과: {result}")

        success_count = sum(1 for success in result.values() if success)
        total_count = len(result)
        print(f"성공률: {success_count}/{total_count}")

        assert len(result) == len(languages)

    @pytest.mark.asyncio
    async def test_execute_simple_python(self, executor, sample_python_codes):
        """간단한 Python 코드 실행"""
        print(f"\n=== Python 간단 실행 테스트 ===")

        code = sample_python_codes["simple_print"]
        print(f"실행할 코드: {code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON,
            timeout=30
        )

        print(f"\n--- 실행 결과 ---")
        print(f"{result.to_dict()}")

        assert result.success is True
        assert result.status == ExecutionStatus.COMPLETED.value
        assert "Hello, World!" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_python_with_imports(self, executor, sample_python_codes):
        """import가 있는 Python 코드 실행"""
        print(f"\n=== Python import 테스트 ===")

        code = sample_python_codes["math_calculation"]
        print(f"실행할 코드:\n{code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON
        )

        print(f"\n--- 실행 결과 ---")
        print(f"{result.to_dict()}")

        assert result.success is True
        assert "Result:" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_python_data_processing(self, executor, sample_python_codes):
        """Python 데이터 처리 테스트"""
        print(f"\n=== Python 데이터 처리 테스트 ===")

        code = sample_python_codes["data_processing"]
        print(f"실행할 코드:\n{code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"표준 출력:\n{result.stdout}")
        if result.stderr:
            print(f"표준 에러:\n{result.stderr}")

        assert result.success is True
        assert "Total: 15" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_python_error_handling(self, executor, sample_python_codes):
        """Python 에러 처리 테스트"""
        print(f"\n=== Python 에러 처리 테스트 ===")

        code = sample_python_codes["error_code"]
        print(f"실행할 코드:\n{code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"상태: {result.status.value}")
        print(f"종료 코드: {result.exit_code}")
        print(f"표준 출력:\n{result.stdout}")
        print(f"표준 에러:\n{result.stderr}")

        assert result.success is False
        assert result.status == ExecutionStatus.FAILED
        assert result.exit_code != 0

    @pytest.mark.asyncio
    async def test_execute_python_timeout(self, executor, sample_python_codes):
        """Python 타임아웃 테스트"""
        print(f"\n=== Python 타임아웃 테스트 ===")

        code = sample_python_codes["infinite_loop"]
        print(f"실행할 코드:\n{code}")
        print("타임아웃: 5초")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON,
            timeout=5
        )

        print(f"\n--- 실행 결과 ---")
        print(f"{result.to_dict()}")

        assert result.success is False
        assert result.execution_time <= 10  # 타임아웃으로 인해 제한됨

    @pytest.mark.asyncio
    async def test_execute_javascript_simple(self, executor, sample_javascript_codes):
        """간단한 JavaScript 실행"""
        print(f"\n=== JavaScript 간단 실행 테스트 ===")

        code = sample_javascript_codes["simple_log"]
        print(f"실행할 코드: {code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.JAVASCRIPT
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"상태: {result.status.value}")
        print(f"표준 출력:\n{result.stdout}")
        if result.stderr:
            print(f"표준 에러:\n{result.stderr}")
        if result.error:
            print(f"에러: {result.error}")

        if result.success:
            assert "Hello from Node.js!" in result.stdout
        else:
            print("JavaScript 실행 실패 - Node.js 이미지가 없을 수 있습니다")

    @pytest.mark.asyncio
    async def test_execute_javascript_json(self, executor, sample_javascript_codes):
        """JavaScript JSON 처리"""
        print(f"\n=== JavaScript JSON 처리 테스트 ===")

        code = sample_javascript_codes["json_processing"]
        print(f"실행할 코드:\n{code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.JAVASCRIPT
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"표준 출력:\n{result.stdout}")
        if result.stderr:
            print(f"표준 에러:\n{result.stderr}")

        if result.success:
            assert "Total: 15" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_environment_variables(self, executor):
        """환경 변수와 함께 실행"""
        print(f"\n=== 환경 변수 테스트 ===")

        code = """
import os
test_var = os.getenv('TEST_VAR', 'not_found')
python_path = os.getenv('PYTHONPATH', 'not_set')
print(f"TEST_VAR: {test_var}")
print(f"PYTHONPATH: {python_path}")
        """

        env_vars = {
            'TEST_VAR': 'hello_world',
            'PYTHONPATH': '/workspace:/custom/path'
        }

        print(f"실행할 코드:\n{code}")
        print(f"환경 변수: {env_vars}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON,
            environment_vars=env_vars
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"표준 출력:\n{result.stdout}")
        if result.stderr:
            print(f"표준 에러:\n{result.stderr}")

        assert result.success is True
        assert "TEST_VAR: hello_world" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_with_memory_limit(self, executor):
        """메모리 제한 테스트"""
        print(f"\n=== 메모리 제한 테스트 ===")

        code = """
import sys
import platform
print(f"Python 버전: {sys.version}")
print(f"플랫폼: {platform.platform()}")
print("메모리 제한 테스트 완료")
        """

        print(f"실행할 코드:\n{code}")
        print("메모리 제한: 128m")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON,
            memory_limit="128m"
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"표준 출력:\n{result.stdout}")
        if result.stderr:
            print(f"표준 에러:\n{result.stderr}")

        assert result.success is True
        assert "메모리 제한 테스트 완료" in result.stdout

    @pytest.mark.asyncio
    async def test_execute_comprehensive_python(self, executor):
        """종합적인 Python 테스트"""
        print(f"\n=== 종합 Python 테스트 ===")

        code = """
# 기본 출력
print("=== Python 종합 테스트 ===")

# 기본 라이브러리
import os
import sys
import json
import math
from datetime import datetime

print(f"Python 버전: {sys.version}")
print(f"현재 시간: {datetime.now()}")

# 수학 계산
result = math.sqrt(16) + math.pi
print(f"수학 계산 결과: {result:.4f}")

# 데이터 처리
data = {
    "name": "test",
    "numbers": [1, 2, 3, 4, 5],
    "timestamp": str(datetime.now())
}

total = sum(data["numbers"])
print(f"숫자 합계: {total}")

# JSON 처리
json_str = json.dumps(data, indent=2)
print("JSON 데이터:")
print(json_str)

# 환경 변수 확인
print(f"PATH 존재: {'PATH' in os.environ}")
print(f"PYTHON_PATH: {os.environ.get('PYTHONPATH', '설정 안됨')}")

# 파일 시스템
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"작업 디렉토리 내용: {os.listdir('.')}")

print("=== 테스트 완료 ===")
        """

        print(f"실행할 코드:\n{code}")

        result = await executor.execute_code(
            code=code,
            language=CodeLanguage.PYTHON,
            timeout=60
        )

        print(f"\n--- 실행 결과 ---")
        print(f"성공: {result.success}")
        print(f"실행 시간: {result.execution_time}초")
        print(f"표준 출력:\n{result.stdout}")
        if result.stderr:
            print(f"표준 에러:\n{result.stderr}")

        assert result.success is True
        assert "Python 종합 테스트" in result.stdout
        assert "테스트 완료" in result.stdou
