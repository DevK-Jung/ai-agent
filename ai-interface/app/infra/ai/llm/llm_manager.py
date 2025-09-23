import logging
import time
import uuid
from typing import AsyncGenerator, Optional, Dict, Any

from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_ollama import ChatOllama

from app.core.config.settings import Settings
from .constants import LLMProvider
from .schemas import LLMRequest, LLMResponse, ChatMessage, ModelConfig, LLMMetadata
from ..prompt.constants import PromptRole
from ..prompt.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class LLMManager:
    def __init__(self, settings: Settings, prompt_manager: PromptManager):
        self.prompt_manager = prompt_manager
        self.settings = settings

    def _create_conversation_id(self):
        return str(uuid.uuid4())

    def _get_system_prompt(self, domain: str, parameters: Optional[Dict[str, Any]]):
        try:
            return self.prompt_manager.get_system_prompt(
                domain,
                parameters
            )
        except ValueError as e:
            raise ValueError(f"Failed to get system prompt: {str(e)}")

    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """LLM 응답을 생성합니다. (blocking/완전 응답)"""

        # 시스템 프롬프트 가져오기
        system_prompt = self._get_system_prompt(request.domain, request.parameters)

        # 동적으로 모델 생성
        model = self._create_model(request.provider, request.llm_config)

        self._append_file_content(request)

        # 메시지 변환
        messages = self._convert_to_langchain_messages(request.messages, system_prompt)

        # LLM 호출 (blocking)
        try:
            start_time = time.time()
            response = await model.ainvoke(messages)
            end_time = time.time()

            return LLMResponse(
                conversation_id=self._create_conversation_id(),
                content=response.content,
                metadata=LLMMetadata(
                    model=model.model,
                    domain=request.domain,
                    response_time=round(end_time - start_time, 2)
                )
            )

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise RuntimeError(f"Failed to generate response: {str(e)}")

    async def generate_response_stream(self, request: LLMRequest) -> AsyncGenerator[LLMResponse, None]:
        """LLM 스트리밍 응답을 생성합니다."""
        self._append_file_content(request)

        # 시스템 프롬프트 가져오기
        system_prompt = self._get_system_prompt(request.domain, request.parameters)

        # 동적으로 모델 생성
        model = self._create_model(request.provider, request.llm_config)

        # 메시지 변환
        messages = self._convert_to_langchain_messages(request.messages, system_prompt)

        conversation_id = self._create_conversation_id()
        # LLM 스트리밍 호출
        try:
            async for chunk in model.astream(messages):
                # if hasattr(chunk, 'content') and chunk.content:
                yield LLMResponse(
                    conversation_id=conversation_id,
                    content=chunk.content
                )

        except Exception as e:
            logger.error(f"Failed to generate streaming response: {e}")
            raise RuntimeError(f"Failed to generate streaming response: {str(e)}")

    def _append_file_content(self, request: LLMRequest):
        if request.file_info:
            # 사용자 메시지 뒤에 붙여줌
            request.messages.append(ChatMessage(
                role=PromptRole.USER.value,
                content=f"사용자가 업로드한 파일 내용입니다:\n\n{request.file_info}"
            ))

    def _create_model(self, provider: LLMProvider, config: ModelConfig):
        """요청에 따라 동적으로 모델을 생성합니다."""

        if not config:
            config = ModelConfig(
                model_name=self.settings.ollama_default_model,
                temperature=self.settings.default_temperature,
            )

        try:
            return ChatOllama(
                model=config.model_name if config.model_name else self.settings.base_model,
                base_url=self.settings.ollama_base_url,
                temperature=config.temperature,
                top_k=config.top_k,
                top_p=config.top_p,
                repeat_penalty=config.repeat_penalty,
                stop=config.stop,
            )

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
