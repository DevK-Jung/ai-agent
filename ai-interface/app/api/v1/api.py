"""
API v1 메인 라우터
모든 v1 엔드포인트들을 통합하고 관리하는 중앙 라우터
"""

from fastapi import APIRouter

# v1/__init__.py에서 정의한 라우터들을 가져옴
from . import endpoints

# from ..deps import get_current_user, get_optional_user, rate_limit_dependency
# from app.models.user import User

# v1 API 메인 라우터 생성
api_router = APIRouter()

# =============================================================================
# 각 엔드포인트 라우터들을 메인 라우터에 포함
# v1/__init__.py에서 정의한 별칭들 사용
# =============================================================================

# # 채팅 관련 엔드포인트
# api_router.include_router(
#     endpoints.chat_router,
#     prefix="/chat",
#     tags=["Chat"],
#     dependencies=[Depends(rate_limit_dependency)]
# )

# 헬스체크 엔드포인트 (인증 불필요)
api_router.include_router(
    endpoints.health_router,
    prefix="/health",
    tags=["Health V1"]
)

# 벡터 관리 엔드포인트
# api_router.include_router(
#     endpoints.vector_router,
#     prefix="/vector",
#     tags=["Vector V1"]
# )

# 벡터 관리 엔드포인트
api_router.include_router(
    endpoints.code_router,
    prefix="/code",
    tags=["code V1"]
)

# 파일 관리 엔드포인트
api_router.include_router(
    endpoints.file_router,
    prefix="/files",
    tags=["file V1"]
)

# LLM 관리 엔드포인트
api_router.include_router(
    endpoints.llm_router,
    prefix="/llm",
    tags=["LLM V1"]
)

api_router.include_router(
    endpoints.collection_router,
    prefix="/collections",
    tags=["Collection V1"]
)


# =============================================================================
# API v1 공통 엔드포인트들
# =============================================================================

@api_router.get("/", summary="API v1 루트", tags=["Root"])
async def api_v1_root():
    """API v1의 루트 엔드포인트"""
    return {
        "message": "AI Interface API v1",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            # "chat": "/api/v1/chat",
            # "models": "/api/v1/models",
            "health": "/api/v1/health",
            # "upload": "/api/v1/upload"
        }
    }

# @api_router.get("/me", summary="현재 사용자 정보", tags=["User"])
# async def get_current_user_info(
#         current_user: User = Depends(get_current_user)
# ):
#     """현재 인증된 사용자의 정보 반환"""
#     return {
#         "user_id": current_user.id,
#         "email": current_user.email,
#         "is_admin": current_user.is_admin,
#         "created_at": current_user.created_at
#     }
#
#
# @api_router.get("/status", summary="API 상태 정보", tags=["Status"])
# async def get_api_status(
#         user: Optional[User] = Depends(get_optional_user)
# ):
#     """API 전체 상태 정보"""
#     basic_status = {
#         "status": "operational",
#         "version": "1.0.0",
#         "available_endpoints": 4,
#         "authenticated": user is not None
#     }
#
#     if user:
#         basic_status.update({
#             "available_models": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
#             "rate_limits": {
#                 "requests_per_minute": 60,
#                 "requests_per_hour": 1000
#             }
#         })
#
#     return basic_status
