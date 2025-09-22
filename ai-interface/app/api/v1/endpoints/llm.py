from fastapi import APIRouter

from app.domains.llm import SimpleChatRequest, LLMServiceResponse
from app.domains.llm.dependencies import LLMServiceDep

router = APIRouter()


@router.post("/chat_simple", response_model=LLMServiceResponse)
async def chat_simple(request: SimpleChatRequest, llm_service: LLMServiceDep):
    return await llm_service.chat_simple(request)
