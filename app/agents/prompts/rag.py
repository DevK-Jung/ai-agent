# prompts/rag.py
"""CRAG Sub-Agent 프롬프트 템플릿"""

from langchain_core.prompts import ChatPromptTemplate

# === 쿼리 재작성 ===
REWRITE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 검색 최적화 전문가입니다.
대화 이력과 현재 쿼리를 분석하여 두 가지를 반환하세요.

1. **rewritten_query**: 벡터 유사도 검색에 최적화된 독립적인 문장 (맥락이 없어도 이해 가능해야 함)
2. **keywords**: pg_bigm 키워드 검색용 핵심 단어 목록 (2-5개, 명사/고유명사 위주)

재시도 횟수(attempt)가 1 이상이면 이전 쿼리보다 더 넓거나 다른 관점의 표현을 사용하세요."""),
    ("human", """대화 이력:
{messages}

현재 검색 쿼리 (attempt {attempt}):
{current_query}"""),
])

# === 내부 검색 관련성 판단 ===
INTERNAL_RELEVANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 검색 결과의 관련성을 판단하는 전문가입니다.
사용자 질문과 검색된 컨텍스트를 비교하여 관련성을 판단하세요.

- **relevant**: 컨텍스트가 질문에 답하기에 충분한 정보를 포함함
- **unrelevant**: 컨텍스트가 질문과 관련이 없거나 정보가 불충분함"""),
    ("human", """질문: {query}

검색된 컨텍스트:
{context}"""),
])

# === 웹 검색 관련성 판단 ===
WEB_RELEVANCE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 웹 검색 결과의 관련성을 판단하는 전문가입니다.
사용자 질문과 웹 검색 결과를 비교하여 관련성을 판단하세요.

- **relevant**: 웹 검색 결과가 질문에 답하기에 충분한 정보를 포함함
- **irrelevant**: 웹 검색 결과가 질문과 관련이 없거나 답변에 사용하기 부적절함"""),
    ("human", """질문: {query}

웹 검색 결과:
{context}"""),
])

# === 최종 답변 생성 ===
ANSWER_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 문서 기반 질의응답 전문 AI 어시스턴트입니다.

<instructions>
- 제공된 컨텍스트를 기반으로 정확하고 유용한 답변을 제공하세요
- 컨텍스트에 없는 내용은 추측하지 마세요
- 답변 마지막에 출처를 명시하세요:
  - 내부 문서(internal): "출처: [파일명]" 형식
  - 웹 검색(web): "출처: [URL]" 형식
</instructions>

<context>
{rag_context}
</context>

<citations>
{citations}
</citations>

<search_source>
{search_source}
</search_source>"""),
    ("placeholder", "{messages}"),
])
