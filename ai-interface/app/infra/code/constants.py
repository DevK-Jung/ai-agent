# app/infra/code/constants.py
from enum import Enum


class ExecutionEnvironment(Enum):
    """코드 실행 환경"""
    DOCKER = "docker"
    LOCAL = "local"
    SANDBOX = "sandbox"


class CodeLanguage(Enum):
    """지원하는 코드 언어"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    R = "r"
    SQL = "sql"


# 기본 설정값
DEFAULT_TIMEOUT = 30  # 초
DEFAULT_MEMORY_LIMIT = "512m"
DEFAULT_CPU_LIMIT = 0.5  # CPU 사용률 50%

# 보안 설정
ALLOWED_PACKAGES = {
    "numpy", "pandas", "matplotlib", "seaborn", "plotly",
    "scipy", "sklearn", "requests", "beautifulsoup4",
    "pillow", "opencv-python", "tensorflow", "torch"
}

FORBIDDEN_IMPORTS = {
    "os", "sys", "subprocess", "socket", "urllib",
    "shutil", "pickle", "marshal", "eval", "exec"
}
