from typing import List

from fastapi import APIRouter, UploadFile, File, Depends
from sse_starlette import EventSourceResponse

from app.domains.file.dependencies import FileServiceDep
from app.domains.llm import SimpleChatRequest, ChatResponse, ChatRequest, DomainInfo
from app.domains.llm.dependencies import LLMServiceDep
from app.domains.llm.schemas import as_form
from app.infra.ai.llm.schemas import LLMResponse

router = APIRouter()


@router.post("/chat_simple", response_model=ChatResponse)
async def chat_simple(request: SimpleChatRequest, llm_service: LLMServiceDep):
    return await llm_service.chat_simple(request)


@router.post("/chat/blocking", response_model=ChatResponse)
async def chat_blocking(llm_service: LLMServiceDep,
                        file_service: FileServiceDep,
                        request: ChatRequest = Depends(as_form),
                        file: UploadFile = File(None, description="파일")):
    file_content = await file_service.extract_file_content(file)

    return await llm_service.chat_blocking(request, file_content)


@router.post("/chat/streaming",
             response_model=LLMResponse,
             response_class=EventSourceResponse)
async def chat_streaming(llm_service: LLMServiceDep,
                         file_service: FileServiceDep,
                         request: ChatRequest = Depends(as_form),
                         file: UploadFile = File(None, description="파일")):
    file_content = await file_service.extract_file_content(file)

    return EventSourceResponse(llm_service.chat_streaming(request, file_content))


@router.post("/available-domains", response_model=List[DomainInfo])
async def available_domains(llm_service: LLMServiceDep):
    return await llm_service.available_domains()


@router.post("/reload-prompts")
async def reload_prompts(llm_service: LLMServiceDep):
    return await llm_service.reload_prompts()
