"""오디오 전사 노드 - WhisperX를 사용한 STT와 화자 분리"""

import os
from typing import Dict, Any

import torch
import whisperx
from whisperx.diarize import DiarizationPipeline

from app.agents.state import MeetingState
from app.core.config import settings

# WhisperX 모델 캐싱 (모듈 레벨)
_transcription_model = None
_alignment_model = None
_alignment_metadata = None
_diarization_pipeline = None


def _get_device():
    """사용 가능한 디바이스 반환"""
    if hasattr(settings, 'WHISPERX_DEVICE') and settings.WHISPERX_DEVICE:
        return settings.WHISPERX_DEVICE
    return "cuda" if torch.cuda.is_available() else "cpu"


def _get_compute_type():
    """디바이스에 따른 compute type 반환"""
    device = _get_device()
    if device == "cuda":
        return "float16"
    return "int8"


def _load_transcription_model():
    """전사 모델 로드"""
    global _transcription_model
    if _transcription_model is None:
        device = _get_device()
        compute_type = _get_compute_type()
        model_size = getattr(settings, 'WHISPERX_MODEL', 'large-v2')

        _transcription_model = whisperx.load_model(
            model_size,
            device=device,
            compute_type=compute_type
        )
    return _transcription_model


def _load_alignment_model(language: str):
    """정렬 모델 로드"""
    global _alignment_model, _alignment_metadata
    if _alignment_model is None or _alignment_metadata is None:
        device = _get_device()
        _alignment_model, _alignment_metadata = whisperx.load_align_model(
            language_code=language,
            device=device
        )
    return _alignment_model, _alignment_metadata


def _load_diarization_pipeline():
    """화자 분리 파이프라인 로드"""
    global _diarization_pipeline
    if _diarization_pipeline is None:
        device = _get_device()
        hf_token = getattr(settings, 'HF_TOKEN', None)

        if not hf_token:
            raise ValueError("HuggingFace token이 설정되지 않았습니다. HF_TOKEN 환경 변수를 설정하세요.")

        _diarization_pipeline = DiarizationPipeline(
            token=hf_token,
            device=device
        )
    return _diarization_pipeline


async def transcribe_audio(state: MeetingState) -> Dict[str, Any]:
    """
    오디오 파일을 전사하고 화자 분리를 수행합니다.
    
    Args:
        state: MeetingState
        
    Returns:
        Dict containing transcript with speaker diarization
    """
    try:
        audio_file_path = state["audio_file_path"]
        language = getattr(settings, 'WHISPERX_LANGUAGE', 'ko')

        # 파일 존재 확인
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_file_path}")

        # 1. 오디오 로드
        audio = whisperx.load_audio(audio_file_path)

        # 2. 전사 수행
        model = _load_transcription_model()
        result = model.transcribe(audio, batch_size=16)

        # 3. 언어 감지 및 정렬
        detected_language = result.get("language", language)
        align_model, metadata = _load_alignment_model(detected_language)

        result = whisperx.align(
            result["segments"],
            align_model,
            metadata,
            audio,
            device=_get_device(),
            return_char_alignments=False
        )

        # 4. 화자 분리 - torchaudio 사용
        diarization_pipeline = _load_diarization_pipeline()
        diarize_segments = diarization_pipeline(audio)

        # 5. 화자 정보 할당
        result = whisperx.assign_word_speakers(diarize_segments, result)

        # 6. 결과 정리
        transcript_segments = []
        for segment in result["segments"]:
            transcript_segments.append({
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", "").strip(),
                "speaker": segment.get("speaker", "SPEAKER_00")
            })

        return {
            "transcript": transcript_segments,
        }

    except Exception as e:
        print(f"오디오 전사 중 오류 발생: {str(e)}")
        # 오류 발생 시 빈 결과 반환
        return {
            "transcript": [],
        }
