"""전사 결과를 화자별 텍스트로 변환하는 노드"""

import logging
from typing import Dict, Any

from app.agents.state import MeetingState

logger = logging.getLogger(__name__)


async def merge_transcript(state: MeetingState) -> Dict[str, Any]:
    """
    WhisperX 전사 결과를 화자별로 그룹화하여 읽기 쉬운 텍스트로 변환합니다.
    
    Args:
        state: MeetingState containing transcript segments
        
    Returns:
        Dict containing merged_transcript as formatted text
    """
    try:
        transcript_segments = state["transcript"]
        
        if not transcript_segments:
            return {"merged_transcript": "전사된 내용이 없습니다."}
        
        # 화자별로 연속된 발언을 그룹화
        merged_lines = []
        current_speaker = None
        current_text_parts = []
        
        for segment in transcript_segments:
            speaker = segment.get("speaker", "SPEAKER_00")
            text = segment.get("text", "").strip()
            
            if not text:
                continue
                
            # 같은 화자의 연속 발언인 경우 텍스트 추가
            if speaker == current_speaker:
                current_text_parts.append(text)
            else:
                # 이전 화자의 발언 완료 처리
                if current_speaker and current_text_parts:
                    speaker_name = _format_speaker_name(current_speaker)
                    merged_text = " ".join(current_text_parts).strip()
                    if merged_text:
                        merged_lines.append(f"{speaker_name}: {merged_text}")
                
                # 새로운 화자 시작
                current_speaker = speaker
                current_text_parts = [text]
        
        # 마지막 화자 발언 처리
        if current_speaker and current_text_parts:
            speaker_name = _format_speaker_name(current_speaker)
            merged_text = " ".join(current_text_parts).strip()
            if merged_text:
                merged_lines.append(f"{speaker_name}: {merged_text}")
        
        # 최종 텍스트 생성
        if merged_lines:
            merged_transcript = "\n".join(merged_lines)
        else:
            merged_transcript = "유효한 전사 내용이 없습니다."
        
        return {
            "merged_transcript": merged_transcript
        }
        
    except Exception as e:
        logger.error(f"전사 결과 병합 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "merged_transcript": "전사 결과를 처리하는 중 오류가 발생했습니다."
        }


def _format_speaker_name(speaker_id: str) -> str:
    """
    화자 ID를 사용자 친화적인 형태로 변환
    
    Args:
        speaker_id: 원본 화자 ID (예: "SPEAKER_00", "SPEAKER_01")
        
    Returns:
        포맷된 화자 이름 (예: "Speaker 1", "Speaker 2")
    """
    try:
        if speaker_id.startswith("SPEAKER_"):
            # SPEAKER_00 -> Speaker 1, SPEAKER_01 -> Speaker 2 형식으로 변환
            speaker_number = int(speaker_id.split("_")[1]) + 1
            return f"Speaker {speaker_number}"
        else:
            return speaker_id
    except (IndexError, ValueError):
        return speaker_id