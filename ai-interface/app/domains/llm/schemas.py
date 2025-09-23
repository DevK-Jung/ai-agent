from typing import Dict, Any, Optional, List

from fastapi import Form, File, UploadFile
from pydantic import BaseModel, Field

from app.infra.ai.llm.constants import LLMProvider
# Re-export infra schemas for domain use
from app.infra.ai.llm.schemas import (
    ChatMessage,
    ModelConfig,
    LLMResponse
)


class SimpleChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    domain: str = Field(default="example", description="Domain for system prompt")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Template parameters")
    model_name: Optional[str] = Field(default=None, description="Model name to use")
    temperature: Optional[float] = Field(default=0.7, description="Response creativity")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    domain: str = Field(default="general", description="Domain for system prompt")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Template parameters")
    llm_config: Optional[ModelConfig] = Field(default=None, description="Model configuration")
    provider: LLMProvider = Field(default=LLMProvider.OLLAMA, description="LLM provider")


# FormData -> ChatRequest 변환
def as_form(
        messages: List[str] = Form(..., description="사용자 입력 메시지 (여러개 가능)"),
        domain: str = Form("general"),
        parameters: str = Form("{}", description="Template parameters (JSON string)"),
        model_name: str = Form(..., description="모델 이름"),
        temperature: float = Form(0.7),
        max_tokens: Optional[int] = Form(None),
        top_p: Optional[float] = Form(None),
        top_k: Optional[int] = Form(None),
        repeat_penalty: Optional[float] = Form(None),
        stop: Optional[str] = Form(None, description="중지 토큰들 (JSON array string)"),
        provider: LLMProvider = Form(LLMProvider.OLLAMA, description="LLM provider"),
) -> ChatRequest:
    import json

    parameters_parsed = json.loads(parameters)
    stop_parsed = json.loads(stop) if stop else None

    # 들어온 메시지를 전부 user role로 변환
    chat_messages = [ChatMessage(role="user", content=m) for m in messages]

    llm_config = ModelConfig(
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=top_p,
        top_k=top_k,
        repeat_penalty=repeat_penalty,
        stop=stop_parsed,
    )

    return ChatRequest(
        messages=chat_messages,
        domain=domain,
        parameters=parameters_parsed,
        llm_config=llm_config,
        provider=provider,
    )


class DomainInfo(BaseModel):
    name: str = Field(..., description="Domain name")
    description: Optional[str] = Field(default=None, description="Domain description")


class ChatResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: Optional[LLMResponse] = Field(default=None, description="LLM response data")
