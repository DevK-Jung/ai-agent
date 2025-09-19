# app/infra/code/dependencies.py
from typing import Annotated

from fastapi import Depends

from app.core.config.dependencies import SettingsDep
from app.infra.code.executor import DockerCodeExecutor
from app.infra.docker.dependencies import DockerClientDep


def get_docker_code_executor(
        docker_client: DockerClientDep,
        settings: SettingsDep
) -> DockerCodeExecutor:
    """Docker 코드 실행기 인스턴스"""
    return DockerCodeExecutor(docker_client, settings)


# 코드 실행 관련 의존성 타입
CodeExecutorDep = Annotated[DockerCodeExecutor, Depends(get_docker_code_executor)]
