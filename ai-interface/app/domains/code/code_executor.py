import asyncio
import io
import json
import os
import tempfile
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Dict, Any, Optional


class CodeExecutor:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.allowed_imports = {
            # 기본 라이브러리
            'os', 'sys', 'json', 'csv', 'math', 'random', 'datetime', 'time',
            'collections', 'itertools', 'functools', 'operator',
            # 데이터 처리
            'numpy', 'pandas', 'matplotlib', 'seaborn', 'plotly',
            # 웹 관련
            'requests', 'urllib', 'http',
            # 기타
            'pathlib', 're', 'string', 'textwrap',
        }

    async def execute_code(
            self,
            code: str,
            input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """코드를 안전하게 실행"""

        # 보안 체크
        if not self._security_check(code):
            return {
                "success": False,
                "error": "보안상 실행이 금지된 코드입니다",
                "output": "",
                "execution_time": 0
            }

        start_time = time.time()

        try:
            # 메모리 내 실행 시도
            result = await self._execute_in_memory(code, input_data)
            execution_time = time.time() - start_time

            return {
                **result,
                "execution_time": round(execution_time, 3)
            }

        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "execution_time": round(execution_time, 3)
            }

    async def _execute_in_memory(
            self,
            code: str,
            input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """메모리 내에서 코드 실행"""

        # 출력 캡처용 버퍼
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()

        # 실행 컨텍스트 준비
        exec_globals = {
            '__builtins__': __builtins__,
            'print': print,  # print 함수 유지
        }

        # 입력 데이터가 있으면 추가
        if input_data:
            exec_globals.update(input_data)

        exec_locals = {}

        try:
            # 표준 출력/에러를 리다이렉트
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                # 코드 실행 (타임아웃 적용)
                await asyncio.wait_for(
                    self._run_code_async(code, exec_globals, exec_locals),
                    timeout=self.timeout
                )

            output = stdout_buffer.getvalue()
            error_output = stderr_buffer.getvalue()

            # 결과 변수들 수집
            result_vars = {}
            for key, value in exec_locals.items():
                if not key.startswith('_'):
                    try:
                        # JSON 직렬화 가능한 값만 포함
                        json.dumps(value)
                        result_vars[key] = value
                    except (TypeError, ValueError):
                        # 직렬화 불가능한 객체는 문자열로 변환
                        result_vars[key] = str(value)

            return {
                "success": True,
                "output": output,
                "error": error_output if error_output else None,
                "variables": result_vars
            }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"코드 실행이 시간 초과되었습니다 ({self.timeout}초)",
                "output": stdout_buffer.getvalue()
            }
        except Exception as e:
            error_msg = traceback.format_exc()
            return {
                "success": False,
                "error": f"실행 오류: {str(e)}",
                "output": stdout_buffer.getvalue(),
                "traceback": error_msg
            }

    async def _run_code_async(self, code: str, exec_globals: dict, exec_locals: dict):
        """비동기로 코드 실행"""
        loop = asyncio.get_event_loop()

        # CPU 집약적 작업을 별도 스레드에서 실행
        await loop.run_in_executor(
            None,
            lambda: exec(code, exec_globals, exec_locals)
        )

    def _security_check(self, code: str) -> bool:
        """보안 검사"""

        # 금지된 키워드들
        forbidden_keywords = [
            '__import__', 'eval', 'exec', 'compile',
            'open', 'file', 'input', 'raw_input',
            'subprocess', 'os.system', 'os.popen',
            'globals', 'locals', 'vars', 'dir',
            'getattr', 'setattr', 'delattr', 'hasattr',
            'exit', 'quit'
        ]

        # 위험한 모듈들
        dangerous_modules = [
            'subprocess', 'os', 'sys', 'shutil', 'socket',
            'urllib', 'requests', 'ftplib', 'smtplib',
            'pickle', 'marshal', 'shelve'
        ]

        code_lower = code.lower()

        # 금지된 키워드 체크
        for keyword in forbidden_keywords:
            if keyword in code_lower:
                return False

        # 위험한 모듈 import 체크
        for module in dangerous_modules:
            if f'import {module}' in code_lower or f'from {module}' in code_lower:
                return False

        return True

    async def execute_file(self, file_path: str) -> Dict[str, Any]:
        """파일로부터 코드 실행"""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"파일을 찾을 수 없습니다: {file_path}",
                    "output": ""
                }

            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            return await self.execute_code(code)

        except Exception as e:
            return {
                "success": False,
                "error": f"파일 실행 오류: {str(e)}",
                "output": ""
            }

    def save_code_to_file(self, code: str, filename: Optional[str] = None) -> str:
        """코드를 파일로 저장"""
        if not filename:
            # 임시 파일 생성
            with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.py',
                    delete=False,
                    encoding='utf-8'
            ) as f:
                f.write(code)
                return f.name
        else:
            # 지정된 파일명으로 저장
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            return str(file_path)
