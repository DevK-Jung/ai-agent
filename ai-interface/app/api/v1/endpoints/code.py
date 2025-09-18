import logging

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import HTMLResponse
from starlette.templating import Jinja2Templates

from app.domains.code.code_executor import CodeExecutor
from app.domains.code.code_generator import CodeGenerator
from app.domains.code.schemas import CodeResponse, CodeRequest, ExecuteRequest

# 도메인별 의존성 임포트

router = APIRouter()
logger = logging.getLogger(__name__)

code_generator = CodeGenerator()
code_executor = CodeExecutor()

# 초기화 함수
async def initialize_generators():
    """코드 생성기 및 실행기 초기화"""
    await code_generator.initialize()

# 템플릿 설정
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """메인 웹 인터페이스"""
    return templates.TemplateResponse("code.html", {"request": request})

@router.post("/generate-code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    """코드 생성 API"""
    try:
        # 코드 생성기가 초기화되지 않았다면 초기화
        if code_generator.llm is None:
            await code_generator.initialize()

        result = await code_generator.generate_code(
            query=request.query,
            context=request.context,
            modify_existing=request.modify_existing
        )

        return CodeResponse(
            generated_code=result["code"],
            explanation=result["explanation"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute-code")
async def execute_code(request: ExecuteRequest):
    """코드 실행 API"""
    try:
        result = await code_executor.execute_code(
            code=request.code,
            input_data=request.input_data
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))