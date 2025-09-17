# # app/api/deps.py (API 레벨 의존성)
# """API 레벨에서 사용되는 공통 의존성들"""
#
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from typing import Optional
# import jwt
# from app.core.config import settings
# from app.models.user import User
#
# security = HTTPBearer()
#
# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ) -> User:
#     """현재 인증된 사용자 정보 반환"""
#     try:
#         token = credentials.credentials
#         # JWT 토큰 검증 로직
#         payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
#         user_id = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token"
#             )
#         # 실제로는 DB에서 사용자 조회
#         return User(id=user_id, email=payload.get("email"))
#     except jwt.PyJWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token"
#         )
#
# async def get_optional_user(
#     credentials: Optional[HTTPAuthorizationCredentials] = Depends(
#         HTTPBearer(auto_error=False)
#     )
# ) -> Optional[User]:
#     """선택적 사용자 인증"""
#     if credentials is None:
#         return None
#     return await get_current_user(credentials)
#
# async def rate_limit_dependency():
#     """요청 제한 의존성"""
#     # Redis 등을 사용한 레이트 리미팅 구현
#     pass
#
# def require_admin(current_user: User = Depends(get_current_user)) -> User:
#     """관리자 권한 필요"""
#     if not current_user.is_admin:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Admin access required"
#         )
#     return current_user