import logging
import os
import time
from typing import Dict, Any, Optional

from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_community.chat_models import ChatOllama

from app.core.config.settings import Settings
from .schemas import LLMProvider, LLMRequest, LLMResponse, ChatMessage, ModelConfig, LLMMetadata
from ..prompt.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class LLMManager:
    def __init__(self, settings: Settings, prompts_dir: Optional[str] = None):
        self.prompt_manager = PromptManager(prompts_dir)
        self.settings = settings
        self._default_configs = self._load_default_configs()

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """LLM 응답을 생성합니다."""

        # 시스템 프롬프트 가져오기
        try:
            system_prompt = self.prompt_manager.get_system_prompt(
                request.domain,
                request.parameters
            )
        except ValueError as e:
            raise ValueError(f"Failed to get system prompt: {str(e)}")

        # 동적으로 모델 생성
        try:
            model = self._create_model(request.provider, request.llm_config)
        except Exception as e:
            raise ValueError(f"Failed to create model: {str(e)}")

        # 메시지 변환
        messages = self._convert_to_langchain_messages(request.messages, system_prompt)

        # LLM 호출
        try:

            start_time = time.time()

            response = await model.ainvoke(messages)

            end_time = time.time()

            return LLMResponse(
                content=response.content,
                metadata=LLMMetadata(
                    model=request.llm_config.model_name,
                    domain=request.domain,
                    response_time=round(end_time - start_time, 2)
                )
            )

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {str(e)}")

    def _load_default_configs(self) -> Dict[LLMProvider, Dict[str, Any]]:
        """기본 모델 설정을 로드합니다."""
        return {
            LLMProvider.OLLAMA: {
                "model_name": os.getenv("OLLAMA_DEFAULT_MODEL", "llama3.1:8b"),
                "temperature": 0.7,
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            }
        }

    def _create_model(self, provider: LLMProvider, config: ModelConfig):
        """요청에 따라 동적으로 모델을 생성합니다."""
        base_config = self._default_configs.get(provider, {}).copy()

        # ModelConfig로 기본 설정 오버라이드
        # model_params = {
        #     "model": config.model_name,
        #     "temperature": config.temperature or base_config.get("temperature", 0.7)
        # }

        # if config.max_tokens:
        #     model_params["max_tokens"] = config.max_tokens
        # if config.top_p:
        #     model_params["top_p"] = config.top_p
        # if config.stop:
        #     model_params["stop"] = config.stop

        try:
            # if provider == LLMProvider.OLLAMA:
            #     ollama_params = {
            #         "model": config.model_name,
            #         "base_url": base_config.get("base_url", "http://localhost:11434"),
            #         "temperature": config.temperature or 0.7
            #     }
            #
            #     # Ollama 특화 파라미터
            #     if config.top_k:
            #         ollama_params["top_k"] = config.top_k
            #     if config.repeat_penalty:
            #         ollama_params["repeat_penalty"] = config.repeat_penalty
            #     if config.stop:
            #         ollama_params["stop"] = config.stop

            # return ChatOllama(**ollama_params)
            return ChatOllama(
                model=config.model_name,
                base_url=self.settings.ollama_base_url,
                temperature=config.temperature,
                top_k=config.top_k,
                top_p=config.top_p,
                repeat_penalty=config.repeat_penalty,
                stop=config.stop,
            )

            # else:
            #     raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to create model for {provider}: {e}")
            raise RuntimeError(f"Model creation failed: {str(e)}")

    def _convert_to_langchain_messages(self, messages: list[ChatMessage], system_prompt: str) -> list[BaseMessage]:
        """ChatMessage를 LangChain 메시지로 변환합니다."""
        lc_messages = []

        # 시스템 프롬프트 추가
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))

        # 사용자 메시지들 변환
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                lc_messages.append(SystemMessage(content=msg.content))

        return lc_messages

    def get_available_domains(self) -> list:
        """사용 가능한 도메인 목록을 반환합니다."""
        return self.prompt_manager.list_available_domains()

    def reload_prompts(self):
        """프롬프트를 다시 로드합니다."""
        self.prompt_manager.reload_prompts()
