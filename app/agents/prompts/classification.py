"""질문 분류를 위한 프롬프트 템플릿"""

CLASSIFICATION_PROMPT = """다음 사용자 질문을 분류해주세요. 다음 4개 카테고리 중 하나로 분류하세요:

1. FACT: 구체적인 사실이나 정보를 묻는 질문
2. SUMMARY: 요약을 요청하는 질문  
3. COMPARE: 비교를 요청하는 질문
4. EVIDENCE: 근거나 증거를 요구하는 질문

사용자 질문: {user_message}

분류 결과만 응답해주세요 (FACT, SUMMARY, COMPARE, EVIDENCE 중 하나):"""

VALID_QUESTION_TYPES = ["FACT", "SUMMARY", "COMPARE", "EVIDENCE"]
DEFAULT_QUESTION_TYPE = "FACT"