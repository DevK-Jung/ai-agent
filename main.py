from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.endpoints import users, chat
from app.core.config import settings
from app.db.database import init_database, close_database
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
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


@app.get("/")
def read_root():
    return {"message": "AI Agent RAG System", "version": "0.1.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
