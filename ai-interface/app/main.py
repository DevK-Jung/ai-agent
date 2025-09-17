"""
FastAPI AI 인터페이스 메인 애플리케이션
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.api import v1_router
from app.core.config.settings import get_settings
from app.core.utils import setup_logging

# 로깅 설정
# setup_logging()

settings = get_settings()

# 애플리케이션 시작/종료 시 실행될 코드
@asynccontextmanager
async def lifespan(_: FastAPI):
    # 시작 시
    setup_logging()
    print("AI Interface API 시작")
    yield
    # 종료 시  
    print("AI Interface API 종료")


# =============================================================================
# FastAPI 앱 생성 - docs 설정 포함
# =============================================================================

app = FastAPI(
    title="AI Interface API",
    description="FastAPI 기반 AI 인터페이스 - 모든 버전 통합",
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
    CORSMiddleware, # type: ignore
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware, # type: ignore
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

# =============================================================================
# 루트 엔드포인트
# =============================================================================

@app.get("/")
async def root():
    """루트 엔드포인트 - API 버전 정보 제공"""
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

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 에러 핸들러"""
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "요청 데이터가 올바르지 않습니다",
                "details": exc.errors()
            }
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """서버 내부 에러 핸들러"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_server_error",
                "message": "서버 내부 오류가 발생했습니다"
            }
        }
    )


# =============================================================================
# 개발용 실행 함수 - 여기가 main 실행 함수!
# =============================================================================

def run_dev():
    """개발 모드로 서버 실행"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


def run_prod():
    """프로덕션 모드로 서버 실행"""
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="warning",
        workers=4
    )


# Python 스크립트로 직접 실행할 때
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "prod":
        print("프로덕션 모드로 시작")
        run_prod()
    else:
        print("개발 모드로 시작")
        run_dev()
