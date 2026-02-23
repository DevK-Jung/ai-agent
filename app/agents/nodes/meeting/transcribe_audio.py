"""오디오 전사 노드 - WhisperX를 사용한 STT와 화자 분리"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Tuple

import numpy as np
import whisperx

from app.agents.state import MeetingState
from app.core.config import settings
from app.infra.ai.whisperx_manager import WhisperXManager, whisperx_manager

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────

def _get_audio_duration_minutes(audio: np.ndarray) -> float:
    """로드된 오디오 배열의 길이를 분 단위로 반환"""
    return len(audio) / settings.WHISPERX_SAMPLE_RATE / 60.0



def _split_audio(audio: np.ndarray) -> List[Tuple[float, np.ndarray]]:
    """
    오디오를 CHUNK_DURATION_MINUTES 단위로 분할

    Returns:
        List of (time_offset_seconds, chunk_array)
    """
    chunk_samples = settings.WHISPERX_CHUNK_DURATION_MINUTES * 60 * settings.WHISPERX_SAMPLE_RATE
    chunks = []

    for start in range(0, len(audio), chunk_samples):
        time_offset = start / settings.WHISPERX_SAMPLE_RATE
        chunk = audio[start:start + chunk_samples]
        chunks.append((time_offset, chunk))

    return chunks


def _process_chunk(
    chunk: np.ndarray,
    manager: WhisperXManager,
    batch_size: int,
    default_language: str,
) -> List[Dict[str, Any]]:
    """
    단일 오디오 청크 전사 처리

    Returns:
        세그먼트 리스트 (시간 오프셋 미적용 상태)
    """
    model = manager.get_transcription_model()
    result = model.transcribe(chunk, batch_size=batch_size)

    detected_language = result.get("language", default_language)
    align_model, metadata = manager.get_alignment_model(detected_language)

    result = whisperx.align(
        result["segments"],
        align_model,
        metadata,
        chunk,
        device=manager.device,
        return_char_alignments=False,
    )

    diarize_segments = manager.get_diarization_pipeline()(chunk)
    result = whisperx.assign_word_speakers(diarize_segments, result)

    return [
        {
            "start": segment.get("start", 0),
            "end": segment.get("end", 0),
            "text": segment.get("text", "").strip(),
            "speaker": segment.get("speaker", "SPEAKER_00"),
        }
        for segment in result["segments"]
        if segment.get("text", "").strip()
    ]


# ─────────────────────────────────────────────
# 메인 전사 로직
# ─────────────────────────────────────────────

def _transcribe_sync(state: MeetingState, manager: WhisperXManager) -> Dict[str, Any]:
    """
    동기 전사 로직 - run_in_executor에서 실행됩니다.

    Args:
        state: MeetingState
        manager: WhisperXManager

    Returns:
        Dict containing transcript segments
    """
    audio_file_path = state["audio_file_path"]
    default_language = settings.WHISPERX_LANGUAGE

    # 파일 존재 확인
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")

    # 오디오 로드
    logger.info(f"오디오 로드 중: {audio_file_path}")
    audio = whisperx.load_audio(audio_file_path)

    # 길이 확인
    audio_duration = _get_audio_duration_minutes(audio)
    logger.info(f"오디오 길이: {audio_duration:.1f}분")

    if audio_duration > settings.WHISPERX_MAX_DURATION_MINUTES:
        raise ValueError(
            f"오디오 길이가 최대 제한({settings.WHISPERX_MAX_DURATION_MINUTES}분)을 초과합니다: {audio_duration:.1f}분"
        )

    batch_size = settings.WHISPERX_BATCH_SIZE
    logger.info(f"배치 크기: {batch_size}")

    # 청크 분할 여부 결정
    if audio_duration > settings.WHISPERX_LONG_AUDIO_THRESHOLD_MINUTES:
        logger.info(f"긴 오디오 감지 ({audio_duration:.1f}분) → 청크 분할 처리")
        transcript_segments = _transcribe_chunked(audio, manager, batch_size, default_language)
    else:
        logger.info("일반 처리")
        transcript_segments = _process_chunk(audio, manager, batch_size, default_language)

    logger.info(f"전사 완료: {len(transcript_segments)}개 세그먼트")
    return {"transcript": transcript_segments}


def _transcribe_chunked(
    audio: np.ndarray,
    manager: WhisperXManager,
    batch_size: int,
    default_language: str,
) -> List[Dict[str, Any]]:
    """
    긴 오디오를 청크 단위로 분할하여 전사

    Returns:
        시간 오프셋이 보정된 전체 세그먼트 리스트
    """
    chunks = _split_audio(audio)
    logger.info(f"총 {len(chunks)}개 청크로 분할 (청크당 {settings.WHISPERX_CHUNK_DURATION_MINUTES}분)")

    all_segments = []

    for i, (time_offset, chunk) in enumerate(chunks):
        logger.info(f"청크 처리 중: {i + 1}/{len(chunks)} (offset={time_offset:.1f}s)")

        segments = _process_chunk(chunk, manager, batch_size, default_language)

        # 시간 오프셋 보정
        for seg in segments:
            seg["start"] += time_offset
            seg["end"] += time_offset

        all_segments.extend(segments)

    return all_segments


# ─────────────────────────────────────────────
# 비동기 진입점
# ─────────────────────────────────────────────

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
        manager = whisperx_manager
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _transcribe_sync, state, manager)

    except FileNotFoundError as e:
        logger.error(str(e))
        return {"transcript": [], "error": str(e)}

    except ValueError as e:
        logger.error(str(e))
        return {"transcript": [], "error": str(e)}

    except Exception as e:
        logger.error(f"오디오 전사 중 오류 발생: {str(e)}", exc_info=True)
        return {"transcript": [], "error": f"오디오 전사 실패: {str(e)}"}