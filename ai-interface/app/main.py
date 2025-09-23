"""
FastAPI AI 인터페이스 메인 애플리케이션
"""
import multiprocessing

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.api import v1_router
from app.core.config.settings import get_settings
from app.core.exception.global_exception_handler import register_global_exception_handlers
from app.core.lifespan import lifespan
from app.view import view_router

settings = get_settings()

# =============================================================================
# FastAPI 앱 생성 - docs 설정 포함
# =============================================================================

app = FastAPI(
    title="AI Interface API",
    description="FastAPI 기반 AI 인터페이스",
    version="1.0.0",
    # 전체 API docs 설정
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# =============================================================================
# 미들웨어 설정
# =============================================================================

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,  # type: ignore
    minimum_size=1000
)

# =============================================================================
# 정적 파일 서빙 (개발용)
# =============================================================================

# if settings.debug:
#     app.mount("/static", StaticFiles(directory="data/uploads"), name="static")

# =============================================================================
# 라우터 등록 - 버전별
# =============================================================================

# v1 API 등록
app.include_router(
    v1_router,
    prefix="/api/v1",
    tags=["API v1"]
)

# View 라우터 등록
app.include_router(
    view_router,
    tags=["Views"]
)


@app.get("/api")
async def api_info():
    """API 정보 제공"""
    return {
        "message": "AI Interface API",
        "description": "FastAPI 기반 AI 인터페이스",
        "supported_versions": {
            "v1": {
                "url": "/api/v1",
                "status": "active",
                "docs": "/docs#/API%20v1",  # 통합 docs에서 v1 섹션
                "docs_v1_only": "/v1/docs",  # v1 전용 docs
                "features": ["health_check"]
            }
        },
        "documentation": {
            "all_versions": "/docs",  # 모든 버전 통합 문서
            "v1_only": "/v1/docs",  # v1 전용 문서
            "redoc": "/redoc"  # ReDoc 문서
        }
    }


# =============================================================================
# 전역 에러 핸들러
# =============================================================================

register_global_exception_handlers(app)


# =============================================================================
# 서버 실행 함수
# =============================================================================

def run_server():
    """환경에 따라 동적으로 서버 실행"""
    import uvicorn

    # 환경별 설정 자동 적용
    if settings.reload:
        workers = 1
    else:
        workers = multiprocessing.cpu_count()  # CPU 물리/논리 코어 수 반환

    print(f">> AI Interface 서버 시작")
    print(f">> Environment: {settings.environment.value}")
    print(f">> Host: {settings.host}")
    print(f">> Port: {settings.port}")
    print(f">> Log Level: {settings.log_level}")
    print(f">> Debug: {settings.debug}")
    print(f">> Reload: {settings.reload}")
    print(f">> Workers: {workers}")
    print("-" * 50)

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        workers=workers,
        log_level=settings.log_level.lower()
    )


# Python 스크립트로 직접 실행할 때
if __name__ == "__main__":
    run_server()
