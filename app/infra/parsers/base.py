"""
파서 베이스 클래스 및 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List
import logging

from .models import ParsedContent


class BaseParser(ABC):
    """파일 파서 베이스 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def parse(self, file_path: str) -> ParsedContent:
        """
        파일에서 구조화된 콘텐츠를 추출합니다.
        
        Args:
            file_path: 파싱할 파일 경로
            
        Returns:
            ParsedContent: 파싱된 콘텐츠
        """
        pass
    
    @abstractmethod
    def get_supported_mime_types(self) -> List[str]:
        """
        지원하는 MIME 타입 목록을 반환합니다.
        
        Returns:
            List[str]: 지원하는 MIME 타입들
        """
        pass
    
    def validate_file(self, file_path: str) -> bool:
        """
        파일 유효성을 검증합니다.
        
        Args:
            file_path: 검증할 파일 경로
            
        Returns:
            bool: 유효한 파일인지 여부
        """
        try:
            import os
            return os.path.exists(file_path) and os.path.getsize(file_path) > 0
        except Exception as e:
            self.logger.warning(f"파일 유효성 검증 실패: {e}")
            return False