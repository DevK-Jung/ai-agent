from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from pydantic import BaseModel, Field

from app.domains.file.constants import FileType


class BaseFileMetadata(BaseModel):
    """기본 파일 메타데이터"""
    mime_type: str
    file_type: FileType
    original_filename: Optional[str] = None
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    processing_time: Optional[float] = None
    processed_at: Optional[datetime] = None


class PDFMetadata(BaseModel):
    """PDF 메타데이터"""
    title: str = ""
    author: str = ""
    subject: str = ""
    creator: str = ""


class PDFExtractionResult(BaseModel):
    """PDF 추출 결과"""
    content: str = Field(description="추출된 텍스트 내용")
    page_count: int = Field(description="총 페이지 수")
    metadata: PDFMetadata
    file_info: BaseFileMetadata


class DocxMetadata(BaseModel):
    """DOCX 메타데이터"""
    paragraph_count: int
    table_count: int


class DocxExtractionResult(BaseModel):
    """DOCX 추출 결과"""
    content: str = Field(description="전체 텍스트 내용")
    paragraphs: List[str] = Field(description="단락별 텍스트")
    tables: List[List[List[str]]] = Field(description="테이블 데이터")
    metadata: DocxMetadata
    file_info: BaseFileMetadata


class ExcelSheetInfo(BaseModel):
    """Excel 시트 정보"""
    data: List[Dict[str, Any]] = Field(description="시트 데이터")
    columns: List[str] = Field(description="컬럼명 목록")
    shape: tuple[int, int] = Field(description="행, 열 개수")


class ExcelMetadata(BaseModel):
    """Excel 메타데이터"""
    total_sheets: int


class ExcelExtractionResult(BaseModel):
    """Excel 추출 결과"""
    content: Dict[str, ExcelSheetInfo] = Field(description="시트별 데이터")
    sheet_names: List[str] = Field(description="시트명 목록")
    metadata: ExcelMetadata
    file_info: BaseFileMetadata


class CSVMetadata(BaseModel):
    """CSV 메타데이터"""
    row_count: int
    column_count: int
    encoding_used: str


class CSVExtractionResult(BaseModel):
    """CSV 추출 결과"""
    content: List[Dict[str, Any]] = Field(description="CSV 데이터")
    columns: List[str] = Field(description="컬럼명 목록")
    metadata: CSVMetadata
    file_info: BaseFileMetadata


class TextMetadata(BaseModel):
    """텍스트 메타데이터"""
    line_count: int
    character_count: int
    encoding_used: str


class TextExtractionResult(BaseModel):
    """텍스트 추출 결과"""
    content: str = Field(description="텍스트 내용")
    lines: List[str] = Field(description="라인별 텍스트")
    metadata: TextMetadata
    file_info: BaseFileMetadata


class JSONMetadata(BaseModel):
    """JSON 메타데이터"""
    data_type: str = Field(description="JSON 데이터 타입")
    size: int = Field(description="JSON 텍스트 크기")
    encoding_used: str


class JSONExtractionResult(BaseModel):
    """JSON 추출 결과"""
    content: Union[Dict[str, Any], List[Any], str, int, float, bool] = Field(description="JSON 데이터")
    metadata: JSONMetadata
    file_info: BaseFileMetadata


class ImageMetadata(BaseModel):
    """이미지 메타데이터"""
    size: int


class ImageExtractionResult(BaseModel):
    """이미지 추출 결과"""
    content: None = None
    message: str = Field(description="이미지 처리 메시지")
    metadata: ImageMetadata
    file_info: BaseFileMetadata


# Union type for all extraction results
FileExtractionResult = Union[
    PDFExtractionResult,
    DocxExtractionResult,
    ExcelExtractionResult,
    CSVExtractionResult,
    TextExtractionResult,
    JSONExtractionResult,
    ImageExtractionResult
]


class ExtractionError(BaseModel):
    """추출 오류 정보"""
    filename: Optional[str] = None
    success: bool = False
    error: str
    error_type: str
    content: None = None


class MultipleFileExtractionResult(BaseModel):
    """다중 파일 추출 결과"""
    filename: Optional[str]
    success: bool
    data: Optional[FileExtractionResult] = None
    error: Optional[str] = None
    error_type: Optional[str] = None


class FileExtractionResponse(BaseModel):
    """API 응답 스키마"""
    success: bool
    message: str
    data: FileExtractionResult


class MultipleFileExtractionResponse(BaseModel):
    """다중 파일 추출 API 응답"""
    success: bool
    message: str
    data: List[MultipleFileExtractionResult]
    summary: Dict[str, int] = Field(description="처리 요약 정보")


class SupportedTypesResponse(BaseModel):
    """지원 파일 형식 응답"""
    supported_types: List[str]
    supported_extensions: List[str]
    max_file_size_mb: int
    features: Dict[str, str]
