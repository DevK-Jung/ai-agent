# prompts/summary.py
"""대화 요약을 위한 프롬프트 템플릿"""

from langchain_core.prompts import ChatPromptTemplate

CONVERSATION_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 대화 요약 전문가입니다. 아래 대화를 분석하여 핵심 내용을 요약해주세요.

{existing_summary}

<conversation>
{conversation}
</conversation>

<instructions>
- 주요 질문과 답변의 핵심 내용 포함
- 대화의 맥락과 흐름 유지
- 중요한 정보나 결론 포함
- 150토큰 이내로 작성
</instructions>

<output_format>
[요약 내용만 작성, 별도 설명 없이]
</output_format>""")
])
