import logging
from typing import Dict, Any, List, Optional
from enum import Enum

from llama_cloud import AsyncLlamaCloud

from app.core.config import settings


class ProcessingTier(str, Enum):
    """LlamaCloud 처리 티어"""
    FAST = "fast"
    COST_EFFECTIVE = "cost_effective"
    AGENTIC = "agentic"
    AGENTIC_PLUS = "agentic_plus"


class SupportedFileType(str, Enum):
    """지원되는 파일 형식"""
    PDF = "application/pdf"
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    EXCEL_LEGACY = "application/vnd.ms-excel"
    POWERPOINT = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    POWERPOINT_LEGACY = "application/vnd.ms-powerpoint"
    WORD = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    WORD_LEGACY = "application/msword"


class LlamaParserService:
    """LlamaCloud를 사용한 문서 파싱 인프라 서비스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """LlamaCloud 클라이언트 초기화"""
        try:
            if not settings.LLAMA_CLOUD_API_KEY:
                self.logger.warning("LLAMA_CLOUD_API_KEY가 설정되지 않았습니다.")
                return
            
            self.client = AsyncLlamaCloud(api_key=settings.LLAMA_CLOUD_API_KEY)
            self.logger.info("LlamaCloud 클라이언트 초기화 완료")
        except Exception as e:
            self.logger.error(f"LlamaCloud 클라이언트 초기화 실패: {e}")
            self.client = None

    def is_available(self) -> bool:
        """LlamaParser 사용 가능 여부 확인"""
        return self.client is not None

    def is_supported_file_type(self, file_type: str) -> bool:
        """파일 형식 지원 여부 확인"""
        return file_type in [ft.value for ft in SupportedFileType]

    async def parse_to_markdown(
        self, 
        file_path: str, 
        file_type: str,
        tier: ProcessingTier = ProcessingTier.COST_EFFECTIVE
    ) -> Dict[str, Any]:
        """
        파일을 마크다운으로 변환합니다.
        
        Args:
            file_path: 파일 경로
            file_type: 파일 MIME 타입
            tier: 처리 티어
            
        Returns:
            Dict containing conversion results
        """
        if not self.is_available():
            raise RuntimeError("LlamaCloud 서비스를 사용할 수 없습니다.")

        if not self.is_supported_file_type(file_type):
            raise ValueError(f"지원하지 않는 파일 형식: {file_type}")

        try:
            self.logger.info(f"파일 파싱 시작: {file_path} ({file_type})")
            
            # 파일 업로드
            file_obj = await self.client.files.create(
                file=file_path, 
                purpose="parse"
            )
            
            # 파일 형식별 옵션 설정
            output_options = {
                "markdown": {
                    "tables": {
                        "output_tables_as_markdown": True,
                    },
                },
            }
            
            processing_options = {
                "ignore": {
                    "ignore_diagonal_text": True,
                },
                "ocr_parameters": {
                    "languages": ["en", "ko"]
                }
            }
            
            # 파싱 실행
            result = await self.client.parsing.parse(
                file_id=file_obj.id,
                tier=tier.value,
                version="latest",
                output_options=output_options,
                processing_options=processing_options,
                expand=["text", "markdown", "items"],
            )

            return self._process_parse_result(result, file_obj.id, tier.value)

        except Exception as e:
            self.logger.error(f"파일 파싱 실패 ({file_path}): {e}")
            return {
                "success": False,
                "error": str(e),
                "markdown": "",
                "text": "",
                "file_id": None
            }

    def _process_parse_result(self, result, file_id: str, tier: str) -> Dict[str, Any]:
        """파싱 결과 처리"""
        
        # 마크다운 내용 결합
        markdown_content = ""
        if result.markdown and result.markdown.pages:
            for page in result.markdown.pages:
                if page.markdown:
                    markdown_content += page.markdown + "\n\n"

        # 텍스트 내용 결합
        text_content = ""
        if result.text and result.text.pages:
            for page in result.text.pages:
                if page.text:
                    text_content += page.text + "\n\n"

        # 구조화된 항목 통계
        table_count = 0
        image_count = 0
        
        if result.items and result.items.pages:
            for page in result.items.pages:
                for item in page.items:
                    item_type = item.__class__.__name__
                    if "Table" in item_type:
                        table_count += 1
                    elif "Image" in item_type:
                        image_count += 1

        return {
            "success": True,
            "markdown": markdown_content.strip(),
            "text": text_content.strip(),
            "file_id": file_id,
            "tier": tier,
            "page_count": len(result.markdown.pages) if result.markdown else 0,
            "table_count": table_count,
            "image_count": image_count,
            "char_count": len(markdown_content),
        }

    def get_supported_file_types(self) -> List[str]:
        """지원되는 파일 형식 목록 반환"""
        return [ft.value for ft in SupportedFileType]

    def get_processing_tiers(self) -> List[str]:
        """사용 가능한 처리 티어 목록 반환"""
        return [tier.value for tier in ProcessingTier]