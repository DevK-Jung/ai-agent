from typing import List

from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from app.domains.llm import SimpleChatRequest, ChatResponse, ChatRequest, DomainInfo
from app.domains.llm.dependencies import LLMServiceDep
from app.infra.ai.llm.schemas import LLMResponse

router = APIRouter()


@router.post("/chat_simple", response_model=ChatResponse)
async def chat_simple(request: SimpleChatRequest, llm_service: LLMServiceDep):
    return await llm_service.chat_simple(request)


@router.post("/chat/blocking", response_model=ChatResponse)
async def chat_blocking(request: ChatRequest, llm_service: LLMServiceDep):
    return await llm_service.chat_blocking(request)


@router.post("/chat/streaming",
             response_model=LLMResponse,
             response_class=EventSourceResponse)
async def chat_streaming(request: ChatRequest, llm_service: LLMServiceDep):
    return EventSourceResponse(llm_service.chat_streaming(request))


@router.post("/available-domains", response_model=List[DomainInfo])
async def available_domains(llm_service: LLMServiceDep):
    return await llm_service.available_domains()


@router.post("/reload-prompts")
async def reload_prompts(llm_service: LLMServiceDep):
    return await llm_service.reload_prompts()
