# app/infra/code/code_file_manager.py
from pathlib import Path
from app.infra.code.constants import CodeLanguage


class CodeFileManager:
    """코드 파일 관리 담당 클래스"""

    @staticmethod
    def get_file_config(language: CodeLanguage) -> tuple[str, list[str]]:
        """언어별 파일명과 실행 명령어 반환"""
        configs = {
            CodeLanguage.PYTHON: ("script.py", ["python", "/workspace/script.py"]),
            CodeLanguage.JAVASCRIPT: ("script.js", ["node", "/workspace/script.js"]),
            CodeLanguage.R: ("script.R", ["Rscript", "/workspace/script.R"])
        }

        if language not in configs:
            raise ValueError(f"지원하지 않는 언어: {language}")

        return configs[language]

    @staticmethod
    def write_code_file(temp_path: Path, filename: str, code: str) -> Path:
        """코드를 파일로 저장"""
        code_file = temp_path / filename
        code_file.write_text(code, encoding='utf-8')
        return code_file

    @staticmethod
    def get_supported_languages() -> list[CodeLanguage]:
        """지원되는 언어 목록 반환"""
        return [
            CodeLanguage.PYTHON,
            CodeLanguage.JAVASCRIPT,
            CodeLanguage.R
        ]

    @staticmethod
    def is_language_supported(language: CodeLanguage) -> bool:
        """언어 지원 여부 확인"""
        supported = CodeFileManager.get_supported_languages()
        return language in supported