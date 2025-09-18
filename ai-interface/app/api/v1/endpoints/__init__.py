# 각 엔드포인트 모듈들 임포트
from . import health

# 각 모듈의 라우터를 쉽게 접근할 수 있도록 별칭 제공
health_router = health.router

__all__ = [
    "health",
    "health_router",
]