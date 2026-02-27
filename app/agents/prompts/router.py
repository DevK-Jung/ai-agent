# prompts/router.py
"""Router Agent 프롬프트 템플릿"""

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

SUMMARIZE_PROMPT = ChatPromptTemplate.from_messages([
    ("placeholder", "{messages}"),
    ("human", "위 대화를 핵심 내용 중심으로 간결하게 요약해주세요."),
])

AGENT_DETECTION_PROMPT = PromptTemplate.from_template("""다음 사용자 메시지를 분석하여 처리할 에이전트를 선택해주세요.

에이전트 종류:
- chat: 일반 대화, 문서 기반 질의응답, 정보 검색 요청
- meeting: 회의 관련 요청 (회의록 작성, 음성 파일 처리, 회의 내용 요약)

사용자 메시지: {user_message}

에이전트 이름만 응답해주세요 (chat 또는 meeting):""")
