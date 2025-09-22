import logging
from typing import List

from fastapi import HTTPException

from app.core.config.settings import Settings
from app.infra.ai.llm.constants import LLMProvider
from app.infra.ai.llm.llm_manager import LLMManager
from app.infra.ai.llm.schemas import LLMRequest, ModelConfig, ChatMessage
from .schemas import SimpleChatRequest, ChatRequest, DomainInfo, LLMServiceResponse
from ...infra.ai.prompt.constants import PromptRole

logger = logging.getLogger(__name__)


class LLMService:
    """LLM 비즈니스 로직 서비스"""

    def __init__(self, settings: Settings, llm_manager: LLMManager):
        self.settings = settings
        self.llm_manager = llm_manager
        self.default_model_name = settings.ollama_default_model

    async def chat_simple(self, request: SimpleChatRequest) -> LLMServiceResponse:
        """간단한 단일 메시지 채팅"""
        try:
            # 기본 모델 설정 생성
            model_config = ModelConfig(
                model_name=request.model_name or self.default_model_name,
                temperature=request.temperature
            )

            # 사용자 메시지를 ChatMessage로 변환
            messages = [ChatMessage(role=PromptRole.USER.value, content=request.message)]

            # LLMRequest 생성
            llm_request = LLMRequest(
                messages=messages,
                domain=request.domain,
                parameters=request.parameters,
                llm_config=model_config,
                provider=LLMProvider.OLLAMA
            )

            # LLM 호출
            response = await self.llm_manager.generate_response(llm_request)

            return LLMServiceResponse(
                success=True,
                message="채팅 응답이 성공적으로 생성되었습니다.",
                data=response
            )

        except ValueError as e:
            logger.error(f"채팅 요청 검증 오류: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            logger.error(f"LLM 응답 생성 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="응답 생성 중 오류가 발생했습니다.")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="서비스 오류가 발생했습니다.")

    async def chat_multi_turn(self, request: ChatRequest) -> LLMServiceResponse:
        """다중 턴 채팅"""
        try:
            # 모델 설정이 없으면 기본값 사용
            if request.llm_config is None:
                model_config = ModelConfig(
                    model_name=self.default_model_name,
                    temperature=0.7
                )
            else:
                model_config = request.llm_config
                # 모델명이 없으면 기본값 사용
                if not model_config.model_name:
                    model_config.model_name = self.default_model_name

            # LLMRequest 생성
            llm_request = LLMRequest(
                messages=request.messages,
                domain=request.domain,
                parameters=request.parameters,
                llm_config=model_config,
                provider=request.provider
            )

            # LLM 호출
            response = await self.llm_manager.generate_response(llm_request)

            return LLMServiceResponse(
                success=True,
                message="다중 턴 채팅 응답이 성공적으로 생성되었습니다.",
                data=response
            )

        except ValueError as e:
            logger.error(f"다중 턴 채팅 요청 검증 오류: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            logger.error(f"LLM 응답 생성 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="응답 생성 중 오류가 발생했습니다.")
        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="서비스 오류가 발생했습니다.")

    def get_available_domains(self) -> List[DomainInfo]:
        """사용 가능한 도메인 목록 조회"""
        try:
            domain_names = self.llm_manager.get_available_domains()
            return [
                DomainInfo(
                    name=domain,
                    description=f"{domain} 도메인 프롬프트"
                )
                for domain in domain_names
            ]
        except Exception as e:
            logger.error(f"도메인 목록 조회 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="도메인 목록을 가져오는 중 오류가 발생했습니다.")

    def reload_prompts(self) -> dict:
        """프롬프트 다시 로드"""
        try:
            self.llm_manager.reload_prompts()
            return {
                "success": True,
                "message": "프롬프트가 성공적으로 다시 로드되었습니다."
            }
        except Exception as e:
            logger.error(f"프롬프트 리로드 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="프롬프트 리로드 중 오류가 발생했습니다.")

    def get_service_status(self) -> dict:
        """서비스 상태 조회"""
        try:
            domains = self.get_available_domains()
            return {
                "status": "healthy",
                "default_model": self.default_model_name,
                "available_domains": len(domains),
                "domains": [domain.name for domain in domains]
            }
        except Exception as e:
            logger.error(f"서비스 상태 조회 오류: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
