# 각 엔드포인트 모듈들 임포트
from . import health, code, file, llm, collection

# 각 모듈의 라우터를 쉽게 접근할 수 있도록 별칭 제공
health_router = health.router
code_router = code.router
file_router = file.router
llm_router = llm.router
collection_router = collection.router

__all__ = [
    "health_router",
    "code_router",
    "llm_router",
    "collection_router"
]
