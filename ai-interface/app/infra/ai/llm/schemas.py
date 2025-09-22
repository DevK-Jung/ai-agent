from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

from app.infra.ai.llm.constants import LLMProvider


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")


class ModelConfig(BaseModel):
    model_name: str = Field(..., description="모델 이름")
    temperature: Optional[float] = Field(default=0.7, description="Temperature")
    max_tokens: Optional[int] = Field(default=None, description="최대 토큰 수")
    top_p: Optional[float] = Field(default=None, description="Top-p 샘플링")
    top_k: Optional[int] = Field(default=None, description="Top-k 샘플링")
    repeat_penalty: Optional[float] = Field(default=None, description="반복 패널티 (Ollama)")
    stop: Optional[List[str]] = Field(default=None, description="중지 토큰들")


class LLMRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    domain: str = Field(..., description="Domain for system prompt")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Template parameters")
    llm_config: ModelConfig = Field(..., description="Model configuration")
    provider: LLMProvider = Field(default=LLMProvider.OLLAMA, description="LLM provider")


class LLMMetadata(BaseModel):
    model: str = Field(..., description="gemma3:27b")
    domain: str = Field(..., description="domain")
    response_time: float = Field(..., description="response_time")


class LLMResponse(BaseModel):
    conversation_id: str = Field(..., description="conversation_id")
    content: str = Field(..., description="Generated response")
    metadata: LLMMetadata = Field(default=None, description="Additional metadata")