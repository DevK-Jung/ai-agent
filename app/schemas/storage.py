"""
Storage 관련 스키마
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileUploadResult:
    """파일 업로드 결과"""
    file_path: str
    content_hash: str
    file_size: int
    
    @property
    def file_path_obj(self) -> Path:
        """Path 객체로 반환"""
        return Path(self.file_path)