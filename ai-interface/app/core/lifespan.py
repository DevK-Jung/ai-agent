from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.utils import setup_logging
from app.infra.docker.dependencies import get_docker_client


@asynccontextmanager
async def lifespan(_: FastAPI):
    """애플리케이션 라이프사이클 관리"""

    # 시작 시 초기화
    setup_logging()
    print("AI Interface API 시작")

    # Docker 클라이언트 초기화
    docker_client = get_docker_client()
    if docker_client.is_available():
        print(">> Docker 클라이언트 초기화 완료")
    else:
        print(">> Docker 클라이언트 사용 불가능")

    # 여기서 다른 초기화 작업들도 추가 가능
    # - 데이터베이스 연결
    # - 캐시 연결
    # - 외부 API 클라이언트 초기화 등

    yield

    # 종료 시 정리
    print("AI Interface API 종료 시작")

    # Docker 클라이언트 정리
    try:
        docker_client.close()
        print(">> Docker 클라이언트 정리 완료")
    except Exception as e:
        print(f">> Docker 클라이언트 정리 실패: {e}")

    # 여기서 다른 정리 작업들도 추가 가능
    # - 데이터베이스 연결 해제
    # - 캐시 연결 해제
    # - 백그라운드 태스크 정리 등

    print("AI Interface API 종료 완료")
