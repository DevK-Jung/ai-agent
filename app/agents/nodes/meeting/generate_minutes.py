"""회의록 생성 노드 - LLM을 사용한 회의록 작성"""

from typing import Dict, Any

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from app.agents.state import MeetingState
from app.agents.prompts.meeting import MEETING_MINUTES_PROMPT
from app.core.config import settings

# LLM 인스턴스 (모듈 레벨에서 생성)
llm = ChatOpenAI(
    model=getattr(settings, 'MINUTES_MODEL', settings.GENERATOR_MODEL),
    temperature=getattr(settings, 'MINUTES_TEMPERATURE', 0.3),
    api_key=settings.OPENAI_API_KEY,
    tags=["MEETING_MINUTES"]
)

# LCEL 체인 구성
minutes_chain = MEETING_MINUTES_PROMPT | llm | StrOutputParser()


async def generate_minutes(state: MeetingState) -> Dict[str, Any]:
    """
    전사된 회의 내용을 바탕으로 구조화된 회의록을 생성합니다.
    
    Args:
        state: MeetingState containing merged_transcript
        
    Returns:
        Dict containing generated meeting minutes
    """
    try:
        merged_transcript = state.get("merged_transcript", "")
        
        if not merged_transcript or merged_transcript.strip() == "":
            return {
                "minutes": "회의록을 생성할 전사 내용이 없습니다."
            }
        
        # 전사 내용이 너무 짧은 경우 체크
        if len(merged_transcript.strip()) < 50:
            return {
                "minutes": "회의록 생성을 위한 충분한 내용이 없습니다. 더 긴 회의 내용이 필요합니다."
            }
        
        # LLM을 통한 회의록 생성
        minutes = await minutes_chain.ainvoke({
            "transcript": merged_transcript
        })
        
        # 생성된 회의록 검증
        if not minutes or len(minutes.strip()) < 100:
            return {
                "minutes": "회의록 생성 중 문제가 발생했습니다. 전사 내용을 다시 확인해주세요."
            }
        
        return {
            "minutes": minutes.strip()
        }
        
    except Exception as e:
        print(f"회의록 생성 중 오류 발생: {str(e)}")
        return {
            "minutes": f"회의록 생성 중 오류가 발생했습니다: {str(e)}"
        }