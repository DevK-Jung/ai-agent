"""답변 생성을 위한 프롬프트 템플릿"""

TYPE_INSTRUCTIONS = {
    "FACT": "구체적이고 정확한 정보를 제공해주세요.",
    "SUMMARY": "핵심 내용을 간결하게 요약해주세요.",
    "COMPARE": "비교 대상들의 차이점과 유사점을 명확히 설명해주세요.",
    "EVIDENCE": "주장에 대한 근거와 출처를 포함해 답변해주세요."
}

ANSWER_GENERATION_PROMPT = """당신은 도움이 되는 AI 어시스턴트입니다.

질문 유형: {question_type}
지침: {instruction}

사용자 질문: {user_message}

한국어로 친절하고 정확한 답변을 제공해주세요:"""

DEFAULT_INSTRUCTION = TYPE_INSTRUCTIONS["FACT"]
ERROR_MESSAGE = "죄송합니다. 현재 답변을 생성할 수 없습니다. 잠시 후 다시 시도해주세요."