"""오디오 전사 노드 - WhisperX를 사용한 STT와 화자 분리"""

import asyncio
import logging
import os
from typing import Any, Dict

import whisperx

from app.agents.state import MeetingState
from app.core.config import settings
from app.infra.ai.whisperx_manager import WhisperXManager, whisperx_manager

logger = logging.getLogger(__name__)


def _transcribe_sync(state: MeetingState, manager: WhisperXManager) -> Dict[str, Any]:
    """
    동기 전사 로직 - run_in_executor에서 실행됩니다.

    Args:
        state: MeetingState

    Returns:
        Dict containing transcript with speaker diarization, or error info
    """
    audio_file_path = state["audio_file_path"]
    default_language = settings.WHISPERX_LANGUAGE
    batch_size = settings.WHISPERX_BATCH_SIZE

    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")

    # 1. 오디오 로드
    logger.info(f"오디오 로드 중: {audio_file_path}")
    audio = whisperx.load_audio(audio_file_path)

    # 2. 전사 수행
    model = manager.get_transcription_model()
    result = model.transcribe(audio, batch_size=batch_size)

    # 3. 언어 감지 및 정렬
    detected_language = result.get("language", default_language)
    logger.info(f"감지된 언어: {detected_language}")

    align_model, metadata = manager.get_alignment_model(detected_language)
    result = whisperx.align(
        result["segments"],
        align_model,
        metadata,
        audio,
        device=manager.device,
        return_char_alignments=False,
    )

    # 4. 화자 분리
    diarization_pipeline = manager.get_diarization_pipeline()
    diarize_segments = diarization_pipeline(audio)

    # 5. 화자 정보 할당
    result = whisperx.assign_word_speakers(diarize_segments, result)

    # 6. 결과 정리
    transcript_segments = [
        {
            "start": segment.get("start", 0),
            "end": segment.get("end", 0),
            "text": segment.get("text", "").strip(),
            "speaker": segment.get("speaker", "SPEAKER_00"),
        }
        for segment in result["segments"]
    ]

    logger.info(f"전사 완료: {len(transcript_segments)}개 세그먼트")
    return {"transcript": transcript_segments}


async def transcribe_audio(state: MeetingState) -> Dict[str, Any]:
    """
    오디오 파일을 전사하고 화자 분리를 수행합니다.
    WhisperX의 동기 연산을 run_in_executor로 감싸 event loop 블로킹을 방지합니다.

    Args:
        state: MeetingState

    Returns:
        Dict containing transcript with speaker diarization, or error info
    """
    try:
        # WhisperX 매니저 사용 (lifespan에서 초기화됨)
        manager = whisperx_manager

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe_sync, state, manager)

    except FileNotFoundError as e:
        logger.error(str(e))
        return {"transcript": [], "error": str(e)}

    except Exception as e:
        logger.error(f"오디오 전사 중 오류 발생: {str(e)}", exc_info=True)
        return {"transcript": [], "error": f"오디오 전사 실패: {str(e)}"}
