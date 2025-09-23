"""
View 라우터 - 템플릿 렌더링 관련 엔드포인트
"""
from pathlib import Path

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

# 템플릿 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# 라우터 생성
view_router = APIRouter()


@view_router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """홈 화면 - 채팅/코딩 선택"""
    return templates.TemplateResponse("index.html", {"request": request})


@view_router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    """채팅 화면"""
    return templates.TemplateResponse("chat.html", {"request": request})


@view_router.get("/code", response_class=HTMLResponse)
async def code_page(request: Request):
    """코딩 화면"""
    return templates.TemplateResponse("code.html", {"request": request})
