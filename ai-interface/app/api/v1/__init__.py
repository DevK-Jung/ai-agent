"""API v1 패키지 초기화"""

# endpoints 모듈을 임포트해서 외부에서 사용할 수 있게 함
from . import endpoints

# api.py에서 사용할 메인 라우터
from .api import api_router

__all__ = ["api_router", "endpoints"]