import logging
from enum import Enum
from typing import Any

from llama_cloud import AsyncLlamaCloud

from app.core.config import settings


class ProcessingTier(str, Enum):
    FAST = "fast"
    COST_EFFECTIVE = "cost_effective"
    AGENTIC = "agentic"
    AGENTIC_PLUS = "agentic_plus"


class SupportedFileType(str, Enum):
    PDF = "application/pdf"
    EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    EXCEL_LEGACY = "application/vnd.ms-excel"
    POWERPOINT = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    POWERPOINT_LEGACY = "application/vnd.ms-powerpoint"
    WORD = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    WORD_LEGACY = "application/msword"


class LlamaParserService:

    POLL_INTERVAL = 2      # 초
    MAX_WAIT_SECONDS = 300 # 5분 타임아웃

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        try:
            if not settings.LLAMA_CLOUD_API_KEY:
                self.logger.warning("LLAMA_CLOUD_API_KEY가 설정되지 않았습니다.")
                return
            self.client = AsyncLlamaCloud(api_key=settings.LLAMA_CLOUD_API_KEY)
            self.logger.info("LlamaCloud 클라이언트 초기화 완료")
        except Exception as e:
            self.logger.error(f"LlamaCloud 클라이언트 초기화 실패: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def is_supported_file_type(self, file_type: str) -> bool:
        return file_type in [ft.value for ft in SupportedFileType]

    async def parse_to_markdown(
        self,
        file_path: str,
        file_type: str,
        tier: ProcessingTier = ProcessingTier.COST_EFFECTIVE,
    ) -> dict[str, Any]:
        if not self.is_available():
            raise RuntimeError("LlamaCloud 서비스를 사용할 수 없습니다.")
        if not self.is_supported_file_type(file_type):
            raise ValueError(f"지원하지 않는 파일 형식: {file_type}")

        try:
            # parsing.parse()는 내부적으로 create() → wait_for_completion() → get()을
            # 모두 처리하며 완료된 ParsingGetResponse를 반환합니다 (수동 폴링 불필요)
            with open(file_path, "rb") as f:
                result = await self.client.parsing.parse(
                    upload_file=f,
                    tier=tier.value,
                    version="latest",
                    output_options={
                        "markdown": {
                            "tables": {"output_tables_as_markdown": True},
                        },
                    },
                    processing_options={
                        "ignore": {"ignore_diagonal_text": True},
                        "ocr_parameters": {"languages": ["en", "ko"]},
                    },
                    expand=["text", "markdown", "items"],
                    timeout=float(self.MAX_WAIT_SECONDS),
                )

            self.logger.info(f"파싱 완료: {file_path} (status={result.job.status})")
            return self._process_parse_result(result, tier.value)

        except Exception as e:
            self.logger.error(f"파일 파싱 실패 ({file_path}): {e}")
            return {
                "success": False,
                "error": str(e),
                "markdown": "",
                "text": "",
                "file_id": None,
            }

    def _process_parse_result(self, result, tier: str) -> dict[str, Any]:
        # result: ParsingGetResponse
        # MarkdownPage는 Union[MarkdownPageMarkdownResultPage, MarkdownPageFailedMarkdownPage]
        # success=True인 페이지만 markdown 속성을 가짐
        markdown_content = ""
        if result.markdown and result.markdown.pages:
            for page in result.markdown.pages:
                if page.success and hasattr(page, "markdown"):
                    markdown_content += page.markdown + "\n\n"

        text_content = ""
        if result.text and result.text.pages:
            for page in result.text.pages:
                if hasattr(page, "text"):
                    text_content += page.text + "\n\n"

        table_count = 0
        image_count = 0
        if result.items and result.items.pages:
            for page in result.items.pages:
                if not page.success:
                    continue
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
            "tier": tier,
            "page_count": len(result.markdown.pages) if result.markdown else 0,
            "table_count": table_count,
            "image_count": image_count,
            "char_count": len(markdown_content),
        }