from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import users, chat, documents, search, meeting
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exception_handlers import setup_exception_handlers
from app.db.database import init_database, close_database
from app.agents.infra.checkpointer import setup_checkpointer_tables
from app.infra.ai.whisperx_manager import whisperx_manager
import uvicorn
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()  # 로깅 설정 초기화
    await init_database()
    
    # 체크포인터 테이블 초기화
    try:
        await setup_checkpointer_tables()
        logger.info("Checkpointer tables initialized successfully")
    except Exception as e:
        logger.warning(f"Checkpointer tables setup failed or already exist: {e}")
    
    # WhisperX 모델 초기화
    try:
        await whisperx_manager.initialize()
        app.state.whisperx_manager = whisperx_manager
        logger.info("WhisperX models initialized successfully")
    except Exception as e:
        logger.warning(f"WhisperX models initialization failed: {e}")
        app.state.whisperx_manager = None
    
    yield
    # Shutdown
    await close_database()

app = FastAPI(
    title="AI Agent RAG System",
    description="Agent-based Explainable RAG System",
    version="0.1.0",
    lifespan=lifespan
)

# 예외 핸들러 등록
setup_exception_handlers(app)

# 라우터 등록
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(meeting.router)


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
