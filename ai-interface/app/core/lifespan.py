from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config.settings import get_settings
from app.core.utils import setup_logging
from app.infra.ai.prompt.dependencies import get_prompt_manager
from app.infra.docker.dependencies import get_docker_client
from app.infra.vector_db.dependencies import get_vector_db_client


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

    # 시스템 프롬프트 템플릿 load
    try:
        get_prompt_manager()
        print(">> 시스템 프롬프트 초기화 완료")
    except Exception as e:
        print(f">> 시스템 프롬프트 초기화 실패: {e}")

    # 벡터DB 클라이언트 초기화
    try:
        settings = get_settings()
        vector_client = await get_vector_db_client(settings)

        # 기본 벡터스토어 미리 생성
        await vector_client.get_vectorstore()
        print(">> 벡터DB 클라이언트 초기화 완료")

        # 헬스체크
        if hasattr(vector_client.connection_manager, '_pg_engine'):
            print(">> 벡터DB 연결 상태 정상")

    except Exception as e:
        print(f">> 벡터DB 클라이언트 초기화 실패: {e}")
        raise e

    # 여기서 다른 초기화 작업들도 추가 가능
    # - 캐시 연결
    # - 외부 API 클라이언트 초기화 등

    yield

    # 종료 시 정리
    print("AI Interface API 종료 시작")

    # 벡터DB 클라이언트 정리
    try:
        # 전역 클라이언트 정리
        from app.infra.vector_db.dependencies import _vector_client
        if _vector_client:
            await _vector_client.close()
            print(">> 벡터DB 클라이언트 정리 완료")
    except Exception as e:
        print(f">> 벡터DB 클라이언트 정리 실패: {e}")

    # Docker 클라이언트 정리
    try:
        docker_client.close()
        print(">> Docker 클라이언트 정리 완료")
    except Exception as e:
        print(f">> Docker 클라이언트 정리 실패: {e}")

    # 여기서 다른 정리 작업들도 추가 가능
    # - 캐시 연결 해제
    # - 백그라운드 태스크 정리 등

    print("AI Interface API 종료 완료")
