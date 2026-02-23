"""WhisperX 모델 매니저 - 스레드 안전한 모델 캐싱"""

import asyncio
import logging
import threading
from typing import Any, Optional, Tuple

import torch
import whisperx
from whisperx.diarize import DiarizationPipeline

from app.core.config import settings

logger = logging.getLogger(__name__)


class WhisperXManager:
    """WhisperX 모델들을 관리하는 싱글톤 매니저"""

    def __init__(self):
        self._transcription_model: Optional[Any] = None
        self._alignment_model: Optional[Any] = None
        self._alignment_metadata: Optional[Any] = None
        self._alignment_language: Optional[str] = None
        self._diarization_pipeline: Optional[DiarizationPipeline] = None
        self._alignment_lock = threading.Lock()
        self._device = self._resolve_device()
        self._compute_type = self._resolve_compute_type()

    def _resolve_device(self) -> str:
        """사용 가능한 디바이스 반환"""
        if settings.WHISPERX_DEVICE:
            return settings.WHISPERX_DEVICE
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _resolve_compute_type(self) -> str:
        """디바이스에 따른 compute type 반환"""
        return "float16" if self._device == "cuda" else "int8"

    # -------------------------------------------------------------------------
    # 동기 로드 함수들 (run_in_executor에서 실행)
    # -------------------------------------------------------------------------

    def _load_transcription_model_sync(self):
        """전사 모델 동기 로드"""
        model_size = settings.WHISPERX_MODEL
        logger.info(f"전사 모델 로드 중: {model_size} (device={self._device}, compute_type={self._compute_type})")
        self._transcription_model = whisperx.load_model(
            model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        logger.info("전사 모델 로드 완료")

    def _load_diarization_pipeline_sync(self):
        """화자 분리 파이프라인 동기 로드"""
        if not settings.HF_TOKEN:
            raise ValueError("HuggingFace token이 설정되지 않았습니다. HF_TOKEN 환경 변수를 설정하세요.")

        logger.info(f"화자 분리 파이프라인 로드 중: device={self._device}")
        self._diarization_pipeline = DiarizationPipeline(
            token=settings.HF_TOKEN,
            device=self._device,
        )
        logger.info("화자 분리 파이프라인 로드 완료")

    def _load_alignment_model_sync(self, language: str):
        """정렬 모델 동기 로드 (언어 변경 시 재로드)"""
        logger.info(f"정렬 모델 로드 중: language={language}, device={self._device}")
        self._alignment_model, self._alignment_metadata = whisperx.load_align_model(
            language_code=language,
            device=self._device,
        )
        self._alignment_language = language
        logger.info(f"정렬 모델 로드 완료: {language}")

    # -------------------------------------------------------------------------
    # 초기화 (lifespan에서 호출)
    # -------------------------------------------------------------------------

    async def initialize(self):
        """모델들을 비동기 초기화 - lifespan에서 호출"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._load_transcription_model_sync)
            await loop.run_in_executor(None, self._load_diarization_pipeline_sync)
            logger.info("WhisperX 모델 초기화 완료")
        except Exception as e:
            logger.error(f"WhisperX 모델 초기화 실패: {e}", exc_info=True)
            raise

    # -------------------------------------------------------------------------
    # 모델 반환
    # -------------------------------------------------------------------------

    def get_transcription_model(self) -> Any:
        """전사 모델 반환"""
        if self._transcription_model is None:
            raise RuntimeError("전사 모델이 초기화되지 않았습니다.")
        return self._transcription_model

    def get_alignment_model(self, language: str) -> Tuple[Any, Any]:
        """정렬 모델 반환 (언어별 캐싱, 스레드 안전)"""
        if self._alignment_model is None or self._alignment_language != language:
            with self._alignment_lock:
                # 락 안에서 한 번 더 체크 (double-checked locking)
                if self._alignment_model is None or self._alignment_language != language:
                    self._load_alignment_model_sync(language)
        return self._alignment_model, self._alignment_metadata

    def get_diarization_pipeline(self) -> DiarizationPipeline:
        """화자 분리 파이프라인 반환"""
        if self._diarization_pipeline is None:
            raise RuntimeError("화자 분리 파이프라인이 초기화되지 않았습니다.")
        return self._diarization_pipeline

    @property
    def device(self) -> str:
        return self._device


# 싱글톤 인스턴스
whisperx_manager = WhisperXManager()