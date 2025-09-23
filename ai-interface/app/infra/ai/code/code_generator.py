import logging
import re
from typing import Dict, Optional, Any

from app.core.config.settings import Settings
from ..llm.constants import LLMProvider
from ..llm.llm_manager import LLMManager
from ..llm.schemas import LLMRequest, ModelConfig, ChatMessage
from ..prompt.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


class CodeGenerator:
    """LLM Manager와 Prompt Manager를 활용한 코드 생성기"""

    def __init__(self, llm_manager: LLMManager, prompt_manager: PromptManager, settings: Settings):
        self.llm_manager = llm_manager
        self.prompt_manager = prompt_manager
        self.settings = settings
        self.default_model_name = "gemma3:27b"

    async def generate_code(
            self,
            query: str,
            context: Optional[str] = None,
            modify_existing: bool = False,
            language: str = "python",
            model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """코드 생성 또는 수정"""
        try:
            # 모델 설정
            model_config = ModelConfig(
                model_name=model_name or self.default_model_name,
                temperature=0.1,
                max_tokens=2048
            )

            # 메시지 구성
            if modify_existing and context:
                # 기존 코드 수정
                messages = [
                    ChatMessage(
                        role="user",
                        content=f"""기존 {language} 코드를 수정해주세요.

기존 코드:
```{language}
{context}
```

수정 요청: {query}

다음 형식으로 응답해주세요:
```{language}
# 수정된 코드
```

**변경사항 설명:**
어떤 부분이 어떻게 변경되었는지 설명해주세요."""
                    )
                ]
                domain = "code_modification"
            else:
                # 새 코드 생성
                content = f"""다음 요청에 따라 {language} 코드를 생성해주세요.

요청: {query}
"""
                if context:
                    content += f"\n추가 컨텍스트: {context}\n"

                content += f"""
다음 형식으로 응답해주세요:
```{language}
# 여기에 {language} 코드 작성
```

**설명:**
코드에 대한 간단한 설명을 작성해주세요.

**주의사항:**
1. 코드는 반드시 실행 가능해야 합니다
2. 필요한 import문을 포함해주세요
3. 에러 처리를 포함해주세요
4. 코드에 주석을 적절히 달아주세요
5. 함수나 클래스 사용 시 docstring을 작성해주세요"""

                messages = [ChatMessage(role="user", content=content)]
                domain = "code_generation"

            # LLM 요청 생성
            llm_request = LLMRequest(
                messages=messages,
                domain=domain,
                parameters={"language": language},
                llm_config=model_config,
                provider=LLMProvider.OLLAMA
            )

            # LLM 호출
            response = await self.llm_manager.generate_response(llm_request)

            # 응답에서 코드와 설명 추출
            code, explanation = self._extract_code_and_explanation(response.content, language)

            return {
                "generated_code": code,
                "explanation": explanation,
                "language": language,
                "model_used": model_config.model_name,
                "execution_time": response.metadata.response_time if response.metadata else None,
                "raw_response": response.content
            }

        except Exception as e:
            logger.error(f"코드 생성 실패: {str(e)}")
            raise Exception(f"코드 생성 실패: {str(e)}")

    async def generate_code_streaming(
            self,
            query: str,
            context: Optional[str] = None,
            modify_existing: bool = False,
            language: str = "python",
            model_name: Optional[str] = None
    ):
        """스트리밍 코드 생성"""
        try:
            # 모델 설정
            model_config = ModelConfig(
                model_name=model_name or self.default_model_name,
                temperature=0.1,
                max_tokens=2048
            )

            # 메시지 구성 (위와 동일한 로직)
            if modify_existing and context:
                messages = [
                    ChatMessage(
                        role="user",
                        content=f"""기존 {language} 코드를 수정해주세요.

기존 코드:
```{language}
{context}
```

수정 요청: {query}

다음 형식으로 응답해주세요:
```{language}
# 수정된 코드
```

**변경사항 설명:**
어떤 부분이 어떻게 변경되었는지 설명해주세요."""
                    )
                ]
                domain = "code_modification"
            else:
                content = f"""다음 요청에 따라 {language} 코드를 생성해주세요.

요청: {query}
"""
                if context:
                    content += f"\n추가 컨텍스트: {context}\n"

                content += f"""
다음 형식으로 응답해주세요:
```{language}
# 여기에 {language} 코드 작성
```

**설명:**
코드에 대한 간단한 설명을 작성해주세요."""

                messages = [ChatMessage(role="user", content=content)]
                domain = "code_generation"

            # LLM 요청 생성
            llm_request = LLMRequest(
                messages=messages,
                domain=domain,
                parameters={"language": language},
                llm_config=model_config,
                provider=LLMProvider.OLLAMA
            )

            # 스트리밍 응답
            async for chunk in self.llm_manager.generate_response_stream(llm_request):
                yield chunk

        except Exception as e:
            logger.error(f"스트리밍 코드 생성 실패: {str(e)}")
            raise Exception(f"스트리밍 코드 생성 실패: {str(e)}")

    def _extract_code_and_explanation(self, response: str, language: str) -> tuple[str, str]:
        """응답에서 코드와 설명을 추출"""
        # 코드 블록 추출
        code_pattern = rf'```(?:{language})?\n(.*?)```'
        code_matches = re.findall(code_pattern, response, re.DOTALL)

        if code_matches:
            code = code_matches[0].strip()
        else:
            # 코드 블록이 없으면 전체 응답을 코드로 처리
            code = response.strip()

        # 설명 추출
        explanation_patterns = [
            r'\*\*설명:\*\*(.*?)(?:\*\*|$)',
            r'\*\*변경사항 설명:\*\*(.*?)(?:\*\*|$)',
            r'설명:(.*?)(?:\n\n|$)',
        ]

        explanation = ""
        for pattern in explanation_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                explanation = match.group(1).strip()
                break

        if not explanation:
            # 패턴으로 찾지 못하면 코드 이후 텍스트를 설명으로 사용
            parts = response.split('```')
            if len(parts) > 2:
                explanation = parts[-1].strip()
            else:
                explanation = f"{language.title()} 코드가 생성되었습니다."

        return code, explanation

    async def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            test_request = LLMRequest(
                messages=[ChatMessage(role="user", content="print('Hello, World!')")],
                domain="general",
                parameters={},
                llm_config=ModelConfig(model_name=self.default_model_name),
                provider=LLMProvider.OLLAMA
            )

            response = await self.llm_manager.generate_response(test_request)
            return bool(response.content)

        except Exception as e:
            logger.error(f"연결 테스트 실패: {str(e)}")
            return False
