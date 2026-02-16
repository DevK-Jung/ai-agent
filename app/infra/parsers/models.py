"""
파싱 결과 데이터 모델
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class Table:
    """테이블 데이터 구조"""
    headers: List[str]
    rows: List[List[str]]
    position: Dict[str, int] = field(default_factory=dict)  # page, x, y 등 위치 정보
    metadata: Dict[str, Any] = field(default_factory=dict)  # 추가 메타데이터


@dataclass
class Image:
    """이미지 정보 구조"""
    name: str
    format: str  # PNG, JPEG 등
    size: Dict[str, int] = field(default_factory=dict)  # width, height
    position: Dict[str, int] = field(default_factory=dict)  # page, x, y 등
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedContent:
    """파싱된 콘텐츠 전체 구조"""
    raw_text: str  # 전체 텍스트
    metadata: Dict[str, Any] = field(default_factory=dict)  # 파일 메타데이터
    structure: Dict[str, Any] = field(default_factory=dict)  # 문서 구조 정보
    tables: List[Table] = field(default_factory=list)  # 테이블 데이터
    images: List[Image] = field(default_factory=list)  # 이미지 정보
    
    @property
    def has_tables(self) -> bool:
        """테이블 포함 여부"""
        return len(self.tables) > 0
    
    @property
    def has_images(self) -> bool:
        """이미지 포함 여부"""
        return len(self.images) > 0
    
    @property
    def page_count(self) -> int:
        """페이지 수 (있는 경우)"""
        return self.metadata.get("page_count", 1)