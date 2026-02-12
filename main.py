from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import users, chat, documents
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import init_database, close_database
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()  # 로깅 설정 초기화
    await init_database()
    yield
    # Shutdown
    await close_database()

app = FastAPI(
    title="AI Agent RAG System",
    description="Agent-based Explainable RAG System",
    version="0.1.0",
    lifespan=lifespan
)

# 라우터 등록
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(documents.router)


@app.get("/")
def read_root():
    return {"message": "AI Agent RAG System", "version": "0.1.0"}


if __name__ == "__main__":
    # 개발 모드에서도 로깅 설정 적용
    setup_logging()
    
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.PORT, 
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
