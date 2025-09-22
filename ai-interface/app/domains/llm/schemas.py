from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field

# Re-export infra schemas for domain use
from app.infra.ai.llm.schemas import (
    ChatMessage,
    ModelConfig,
    LLMRequest,
    LLMResponse,
    LLMMetadata
)
from app.infra.ai.llm.constants import LLMProvider


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


class DomainInfo(BaseModel):
    name: str = Field(..., description="Domain name")
    description: Optional[str] = Field(default=None, description="Domain description")


class ChatResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    data: Optional[LLMResponse] = Field(default=None, description="LLM response data")