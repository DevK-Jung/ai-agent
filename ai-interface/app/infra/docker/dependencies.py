from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.infra.docker.client import DockerClient


@lru_cache()
def get_docker_client() -> DockerClient:
    """Docker 클라이언트 싱글톤 인스턴스 반환"""
    return DockerClient()


# 의존성 주입용 타입 어노테이션
DockerClientDep = Annotated[DockerClient, Depends(get_docker_client)]
