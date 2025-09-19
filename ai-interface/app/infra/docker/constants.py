# app/infra/docker/constants.py
from enum import Enum
from app.infra.code.constants import CodeLanguage


class ExecutionStatus(Enum):
    """실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


# Docker 이미지 설정
DOCKER_IMAGES = {
    CodeLanguage.PYTHON: "jupyter/scipy-notebook:latest",
    CodeLanguage.JAVASCRIPT: "node:18-alpine",
    CodeLanguage.R: "rocker/r-base:latest",
}
