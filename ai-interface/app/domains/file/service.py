import asyncio
import hashlib
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import UploadFile, HTTPException

from .file_extractor import FileExtractor
from .schemas import FileExtractionResult
from ...core.config.settings import Settings

logger = logging.getLogger(__name__)


class FileService:
    """파일 처리 비즈니스 로직"""

    def __init__(self, settings: Settings):
        self.max_file_size = settings.max_file_size  # 50MB
        self.allowed_extensions = settings.allowed_extensions_set
        self.executor = ThreadPoolExecutor(max_workers=settings.thread_pool_workers)
        self.max_concurrent_files = settings.max_concurrent_files

    async def extract_file_content(
            self,
            file: UploadFile,
            extract_options: Optional[Dict[str, Any]] = None
    ) -> Optional[FileExtractionResult]:
        """파일 내용 추출 메인 메서드"""
        try:
            # 파일 유효성 검증
            self._validate_file(file)

            # 파일 내용 읽기
            file_content = await file.read()

            if not file_content:
                raise HTTPException(status_code=400, detail="빈 파일입니다.")

            # 파일 정보 로깅
            file_hash = self._calculate_file_hash(file_content)
            logger.info(f"파일 처리 시작: {file.filename}, 크기: {len(file_content)} bytes, 해시: {file_hash[:16]}...")

            # 백그라운드에서 추출 실행
            loop = asyncio.get_event_loop()

            extract_kwargs = extract_options or {}

            func = partial(
                FileExtractor.extract_content,
                file_content,
                file.filename,
                **extract_kwargs
            )

            result = await loop.run_in_executor(
                self.executor,
                func
            )  # type: ignore[arg-type]

            logger.info(f"파일 처리 완료: {file.filename}")

            return result

        except HTTPException:
            raise
        except ValueError as e:
            logger.error(f"파일 추출 오류: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"예상치 못한 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="파일 처리 중 오류가 발생했습니다.")
        finally:
            # 파일 스트림 리셋
            await file.seek(0)

    async def extract_multiple_files(
            self,
            files: List[UploadFile],
            extract_options: Optional[Dict[str, Any]] = None
    ) -> List[FileExtractionResult]:
        """여러 파일 동시 처리"""
        if len(files) > self.max_concurrent_files:  # 동시 처리 파일 수 제한
            raise HTTPException(status_code=400, detail=f"한 번에 최대 {self.max_concurrent_files} 개 파일까지 처리할 수 있습니다.")

        tasks = [
            self.extract_file_content(file, extract_options)
            for file in files
        ]

        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 예외 처리된 결과들을 정리
            processed_results = []
            for i, result in enumerate(results):
                # if isinstance(result, Exception):
                #     processed_results.append({
                #         "filename": files[i].filename,
                #         "success": False,
                #         "error": str(result),
                #         "content": None
                #     })
                # else:
                # result["success"] = True
                processed_results.append(result)

            return processed_results

        except Exception as e:
            logger.error(f"다중 파일 처리 오류: {str(e)}")
            raise HTTPException(status_code=500, detail="파일들을 처리하는 중 오류가 발생했습니다.")

    def _validate_file(self, file: UploadFile) -> None:
        """파일 유효성 검증"""
        # 파일 크기 검증
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기가 너무 큽니다. 최대 {self.max_file_size} MB까지 허용됩니다."
            )

        # 파일 확장자 검증
        if file.filename:
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in self.allowed_extensions:
                raise HTTPException(
                    status_code=400,
                    detail=f"지원하지 않는 파일 형식입니다. 허용되는 형식: {', '.join(self.allowed_extensions)}"
                )

        # MIME 타입 기본 검증
        if file.content_type and not any(
                allowed in file.content_type
                for allowed in ['application/', 'text/', 'image/']
        ):
            raise HTTPException(
                status_code=400,
                detail="지원하지 않는 파일 형식입니다."
            )

    def _calculate_file_hash(self, content: bytes) -> str:
        """파일 해시값 계산 (중복 체크용)"""
        return hashlib.sha256(content).hexdigest()
