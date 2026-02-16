"""
파서 팩토리 - 파일 타입에 따른 적절한 파서 제공
"""
from typing import Dict, Type
from .base import BaseParser
from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .xlsx_parser import XLSXParser
from .csv_parser import CSVParser
from .doc_parser import DOCParser


class ParserFactory:
    """파일 타입별 파서를 생성하는 팩토리 클래스"""
    
    # MIME 타입과 파서 클래스 매핑
    _parsers: Dict[str, Type[BaseParser]] = {
        "application/pdf": PDFParser,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DOCXParser,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": XLSXParser,
        "text/csv": CSVParser,
        "application/csv": CSVParser,
        "application/msword": DOCParser,
        "application/vnd.ms-word": DOCParser,
    }
    
    # 파일 확장자 기반 매핑 (fallback용)
    _extension_mapping = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".doc": "application/msword",
    }
    
    @classmethod
    def get_parser(cls, mime_type: str) -> BaseParser:
        """
        MIME 타입에 해당하는 파서 인스턴스를 반환합니다.
        
        Args:
            mime_type: 파일의 MIME 타입
            
        Returns:
            BaseParser: 해당 파일 타입의 파서 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 파일 형식인 경우
        """
        if mime_type not in cls._parsers:
            raise ValueError(f"지원하지 않는 파일 형식: {mime_type}")
        
        parser_class = cls._parsers[mime_type]
        return parser_class()
    
    @classmethod
    def get_parser_by_extension(cls, file_extension: str) -> BaseParser:
        """
        파일 확장자로부터 파서 인스턴스를 반환합니다.
        
        Args:
            file_extension: 파일 확장자 (.pdf, .docx 등)
            
        Returns:
            BaseParser: 해당 파일 타입의 파서 인스턴스
            
        Raises:
            ValueError: 지원하지 않는 파일 확장자인 경우
        """
        # 확장자를 소문자로 변환
        extension = file_extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        
        if extension not in cls._extension_mapping:
            raise ValueError(f"지원하지 않는 파일 확장자: {extension}")
        
        mime_type = cls._extension_mapping[extension]
        return cls.get_parser(mime_type)
    
    @classmethod
    def is_supported_mime_type(cls, mime_type: str) -> bool:
        """
        해당 MIME 타입이 지원되는지 확인합니다.
        
        Args:
            mime_type: 확인할 MIME 타입
            
        Returns:
            bool: 지원 여부
        """
        return mime_type in cls._parsers
    
    @classmethod
    def is_supported_extension(cls, file_extension: str) -> bool:
        """
        해당 파일 확장자가 지원되는지 확인합니다.
        
        Args:
            file_extension: 확인할 파일 확장자
            
        Returns:
            bool: 지원 여부
        """
        extension = file_extension.lower()
        if not extension.startswith('.'):
            extension = '.' + extension
        return extension in cls._extension_mapping
    
    @classmethod
    def get_supported_mime_types(cls) -> list[str]:
        """
        지원하는 모든 MIME 타입 목록을 반환합니다.
        
        Returns:
            list[str]: 지원하는 MIME 타입들
        """
        return list(cls._parsers.keys())
    
    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """
        지원하는 모든 파일 확장자 목록을 반환합니다.
        
        Returns:
            list[str]: 지원하는 파일 확장자들
        """
        return list(cls._extension_mapping.keys())
    
    @classmethod
    def register_parser(cls, mime_type: str, parser_class: Type[BaseParser], extension: str = None):
        """
        새로운 파서를 등록합니다.
        
        Args:
            mime_type: 파서가 처리할 MIME 타입
            parser_class: 파서 클래스
            extension: 파일 확장자 (선택사항)
        """
        if not issubclass(parser_class, BaseParser):
            raise ValueError("파서 클래스는 BaseParser를 상속해야 합니다.")
        
        cls._parsers[mime_type] = parser_class
        
        if extension:
            if not extension.startswith('.'):
                extension = '.' + extension
            cls._extension_mapping[extension.lower()] = mime_type