from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema.output_parser import StrOutputParser
from typing import Dict, Optional
import re
import json

from app.core.config.settings import get_settings


class CodeGenerator:
    def __init__(self, model_name: str = "codellama"):
        self.model_name = model_name
        self.llm = None
        self.code_chain = None
        self.modify_chain = None
        self.settings = get_settings()

    async def initialize(self):
        """LLM 및 체인 초기화"""
        try:
            # Ollama LLM 초기화
            self.llm = OllamaLLM(
                # model=self.model_name,
                model="gemma3:27b",
                base_url=self.settings.ollama_base_url,
                temperature=0.1
            )

            # 코드 생성 프롬프트 템플릿
            code_prompt = PromptTemplate(
                input_variables=["query", "context"],
                template="""
당신은 숙련된 파이썬 개발자입니다. 사용자의 요청에 따라 깔끔하고 실행 가능한 파이썬 코드를 생성해주세요.

사용자 요청: {query}

{context}

다음 형식으로 응답해주세요:
```python
# 여기에 파이썬 코드 작성
```

**설명:**
코드에 대한 간단한 설명을 작성해주세요.

**주의사항:**
1. 코드는 반드시 실행 가능해야 합니다
2. 필요한 import문을 포함해주세요
3. 에러 처리를 포함해주세요
4. 코드에 주석을 적절히 달아주세요
5. 함수나 클래스 사용 시 docstring을 작성해주세요
"""
            )

            # 코드 수정 프롬프트 템플릿
            modify_prompt = PromptTemplate(
                input_variables=["original_code", "modification_request"],
                template="""
기존 파이썬 코드를 사용자 요청에 따라 수정해주세요.

**기존 코드:**
```python
{original_code}
```

**수정 요청:** {modification_request}

다음 형식으로 응답해주세요:
```python
# 수정된 파이썬 코드
```

**변경사항 설명:**
어떤 부분이 어떻게 변경되었는지 설명해주세요.
"""
            )

            # LLMChain 생성
            self.code_chain = code_prompt | self.llm | StrOutputParser()
            self.modify_chain = modify_prompt | self.llm | StrOutputParser()

        except Exception as e:
            print(f"❌ Failed to initialize CodeGenerator: {e}")
            raise

    async def generate_code(
            self,
            query: str,
            context: Optional[str] = None,
            modify_existing: bool = False
    ) -> Dict[str, str]:
        """코드 생성 또는 수정"""
        try:
            if modify_existing and context:
                # 기존 코드 수정
                response = await self.modify_chain.ainvoke({
                    "original_code": context,
                    "modification_request": query
                })
            else:
                # 새 코드 생성
                context_str = f"추가 컨텍스트: {context}" if context else "컨텍스트가 제공되지 않았습니다."
                response = await self.code_chain.ainvoke({
                    "query": query,
                    "context": context_str
                })

            # 응답에서 코드와 설명 추출
            code, explanation = self._extract_code_and_explanation(response)

            return {
                "code": code,
                "explanation": explanation,
                "raw_response": response
            }

        except Exception as e:
            print(f"❌ Code generation failed: {e}")
            raise Exception(f"코드 생성 실패: {e}")

    def _extract_code_and_explanation(self, response: str) -> tuple[str, str]:
        """응답에서 코드와 설명을 추출"""
        # 코드 블록 추출 (```python ... ``` 또는 ``` ... ```)
        code_pattern = r'```(?:python)?\n(.*?)```'
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
                explanation = "코드가 생성되었습니다."

        return code, explanation

    async def test_connection(self) -> bool:
        """Ollama 연결 테스트"""
        try:
            if not self.llm:
                return False

            test_response = await self.llm.ainvoke("print('Hello, World!')")
            return True
        except Exception as e:
            print(f"❌ Ollama connection test failed: {e}")
            return False

    def get_available_models(self) -> list:
        """사용 가능한 모델 목록 조회"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            print(f"❌ Failed to get available models: {e}")
            return []